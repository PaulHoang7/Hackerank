from __future__ import annotations

import base64
import hashlib
import json
import logging
import mimetypes
import re
from pathlib import Path
from threading import Lock
from time import perf_counter
from typing import Any

import httpx

from app.core.config import Settings
from app.core.exceptions import AppError
from app.models.enums import Verdict
from app.services.ai.base import (
    ClaimVerificationResult,
    QuestionAnswer,
    VideoIntelligenceProvider,
    VideoWindowAnalysis,
    VideoWindowInput,
)


logger = logging.getLogger(__name__)
JSON_FENCE_PATTERN = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)
PLATFORM_PRODUCT_UI_SOURCES = {
    "comment",
    "live_comment",
    "chat",
    "bottom_product_card",
    "product_shelf",
    "shopping_shelf",
    "shopping_cart",
    "platform_product_card",
    "recommendation_card",
    "ui_product_card",
    "ui_shelf",
}
ACTIVE_LIVE_PRODUCT_CARD_SOURCES = {
    "active_live_product_card",
    "left_product_card",
    "top_left_product_card",
    "pinned_live_product_card",
    "live_product_card",
}
PHYSICAL_PRODUCT_SOURCES = {
    "visual_label",
    "physical_label",
    "visible_packaging",
    "visual_shape",
    "host_demo",
    "held_product",
    "spoken_with_visible_product",
    *ACTIVE_LIVE_PRODUCT_CARD_SOURCES,
}
NON_PRODUCT_NAME_PATTERNS = {
    "hannaholala",
    "hannah olala",
    "hannah olala x whoo",
    "whoo x hannah",
    "whoo x hannah olala",
    "whoox hannah",
    "hannah",
}


class SeedOmniVideoIntelligenceProvider(VideoIntelligenceProvider):
    name = "seed_omni"
    _gemini_key_lock = Lock()
    _gemini_key_cursor = 0

    def __init__(self, settings: Settings) -> None:
        if not settings.seed_omni_api_key:
            raise AppError("AI_PROVIDER_NOT_CONFIGURED", "SEED_OMNI_API_KEY is required")
        self.model_name = settings.seed_omni_model or "seed-2-0-mini-260428"
        self._model_names = _unique_model_names([self.model_name, *settings.seed_omni_fallback_models])
        self._api_key = settings.seed_omni_api_key
        self._base_url = settings.seed_omni_base_url.rstrip("/")
        self._timeout = settings.external_api_timeout_seconds
        self._video_fps = settings.seed_omni_video_fps
        self._max_tokens = settings.seed_omni_max_tokens
        self._max_video_bytes = settings.seed_omni_max_video_bytes
        self._thinking_enabled = settings.seed_omni_thinking_enabled
        self._reasoning_effort = settings.seed_omni_reasoning_effort

        self._embedding_provider = settings.embedding_provider
        self._embedding_dimensions = settings.embedding_dimensions

        self._gemini_api_keys = settings.gemini_api_keys
        self._gemini_base_url = settings.gemini_base_url.rstrip("/")
        self._gemini_embedding_model = settings.gemini_embedding_model
        # Gemini emits the unified embedding_dimensions (Matryoshka outputDimensionality)
        # so it fits the existing pgvector column regardless of provider — no migration.
        self._gemini_embedding_dimensions = settings.embedding_dimensions

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(self._timeout, read=self._timeout),
            headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"},
        )

    def _gemini_client(self, api_key: str) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._gemini_base_url,
            timeout=httpx.Timeout(self._timeout, read=self._timeout),
            headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        )

    async def analyze_video_window(self, window: VideoWindowInput) -> VideoWindowAnalysis:
        media_path = window.clip_path or window.local_video_path
        if not media_path.is_file():
            raise AppError("SEED_VIDEO_INPUT_MISSING", "Video window clip is missing")
        if media_path.stat().st_size > self._max_video_bytes:
            raise AppError(
                "SEED_VIDEO_INPUT_TOO_LARGE",
                "Seed Chat API video input must be under the configured byte limit",
                details={"path": str(media_path), "size": media_path.stat().st_size, "limit": self._max_video_bytes},
            )

        prompt = _analysis_prompt(window.start_time, window.end_time)
        payload = self._with_thinking({
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "video_url",
                            "video_url": {
                                "url": _data_url(media_path),
                                "fps": self._video_fps,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            "max_tokens": self._max_tokens,
        })
        data = await self._post_json("/chat/completions", payload)
        message_text = _message_text(data)
        try:
            parsed = _parse_json_object(message_text)
        except AppError as exc:
            if exc.code != "SEED_JSON_PARSE_FAILED":
                raise
            logger.warning(
                "seed_analysis_json_parse_failed video_id=%s start=%s end=%s details=%s",
                window.video_id,
                window.start_time,
                window.end_time,
                exc.details,
            )
            return _fallback_analysis_from_unparseable_response(message_text, window.start_time, window.end_time)
        return _analysis_from_json(parsed, window.start_time, window.end_time)

    async def answer_question(self, video_id: str, question: str, windows: list[dict]) -> QuestionAnswer:
        started = perf_counter()
        prompt = _qa_prompt(question, windows)
        data = await self._post_json(
            "/chat/completions",
            self._with_thinking({
                "model": self.model_name,
                "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
                "max_tokens": self._max_tokens,
            }),
        )
        parsed = _parse_json_object(_message_text(data))
        evidence = parsed.get("evidence") if isinstance(parsed.get("evidence"), list) else []
        return QuestionAnswer(
            answer=str(parsed.get("answer") or "I could not answer from the indexed evidence."),
            latency_ms=int((perf_counter() - started) * 1000),
            estimated_cost=0.0,
            evidence=[
                {
                    "video_window_id": str(item.get("video_window_id") or item.get("window_id") or ""),
                    "timestamp": float(item.get("timestamp") or item.get("start_time") or 0),
                    "rationale": str(item.get("rationale") or item.get("reason") or "Seed selected this evidence."),
                }
                for item in evidence
                if isinstance(item, dict)
            ],
        )

    async def verify_claim(self, claim_text: str, evidence: list[dict]) -> ClaimVerificationResult:
        prompt = _verification_prompt(claim_text, evidence)
        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        for item in evidence[:3]:
            clip_path_value = item.get("local_clip_path") if isinstance(item, dict) else None
            if not clip_path_value:
                continue
            clip_path = Path(str(clip_path_value))
            if not clip_path.is_file() or clip_path.stat().st_size > self._max_video_bytes:
                continue
            content.append({"type": "text", "text": f"Video evidence near timestamp={item.get('timestamp')}:"})
            content.append(
                {
                    "type": "video_url",
                    "video_url": {
                        "url": _data_url(clip_path),
                        "fps": self._video_fps,
                    },
                }
            )
        data = await self._post_json(
            "/chat/completions",
            self._with_thinking({
                "model": self.model_name,
                "messages": [{"role": "user", "content": content}],
                "max_tokens": self._max_tokens,
            }),
        )
        parsed = _parse_json_object(_message_text(data))
        return ClaimVerificationResult(
            verdict=_verdict(parsed.get("verdict")),
            explanation=str(parsed.get("explanation") or parsed.get("reason") or ""),
            confidence=_bounded_float(parsed.get("confidence"), default=0.5),
            evidence_frame_ids=[
                str(item)
                for item in (parsed.get("evidence_frame_ids") or [])
                if isinstance(item, str) and item
            ],
        )

    async def detect_products(self, video_id: str, windows: list[dict]) -> list[dict]:
        candidates = _product_candidates_from_windows(windows)
        if not candidates:
            return []
        try:
            data = await self._post_json(
                "/chat/completions",
                self._with_thinking({
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": [{"type": "text", "text": _product_consolidation_prompt(candidates)}]}],
                    "max_tokens": min(self._max_tokens, 1800),
                }),
            )
            parsed = _parse_json_object(_message_text(data))
            products = _products_from_consolidation(parsed, candidates)
            if products:
                return products
        except Exception:
            pass
        return _fallback_products_from_candidates(candidates)

    async def generate_embedding(self, text: str, *, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
        if self._embedding_provider == "local":
            return await self._generate_local_embedding(text)
        return await self._generate_gemini_embedding(text, task_type=task_type)

    async def _generate_local_embedding(self, text: str) -> list[float]:
        # Symmetric multilingual model — no query/document prefix needed. Runs the
        # blocking encode off the event loop so concurrent chunks don't serialize.
        import asyncio

        from app.services.ai.local_embeddings import embed_text

        vector = await asyncio.to_thread(embed_text, text[:12000])
        expected = self._embedding_dimensions
        if len(vector) != expected:
            raise AppError(
                "LOCAL_EMBEDDING_INVALID_DIMENSIONS",
                "Local embedding dimensions did not match configuration",
                details={"expected": expected, "actual": len(vector)},
            )
        return vector

    async def _generate_gemini_embedding(self, text: str, *, task_type: str) -> list[float]:
        api_keys = self._rotated_gemini_api_keys()
        if not api_keys:
            raise AppError("GEMINI_EMBEDDING_NOT_CONFIGURED", "GEMINI_API_KEYS is required for embeddings")
        model_resource = _gemini_model_resource(self._gemini_embedding_model)
        embedding_task_type = _gemini_task_type(task_type)
        payload = {
            "model": model_resource,
            "content": {"parts": [{"text": text[:12000]}]},
            "taskType": embedding_task_type,
            "outputDimensionality": self._gemini_embedding_dimensions,
            "embedContentConfig": {
                "taskType": embedding_task_type,
                "outputDimensionality": self._gemini_embedding_dimensions,
                "autoTruncate": True,
            },
        }
        last_error: str | None = None
        for index, api_key in enumerate(api_keys):
            try:
                async with self._gemini_client(api_key) as client:
                    response = await client.post(f"/{model_resource}:embedContent", json=payload)
                if response.status_code >= 400:
                    last_error = response.text[-2000:]
                    if response.status_code in {401, 403, 429, 500, 502, 503, 504} and index < len(api_keys) - 1:
                        continue
                    raise AppError(
                        "GEMINI_EMBEDDING_ERROR",
                        "Gemini embedding request failed",
                        response.status_code,
                        details=last_error,
                    )
                data = response.json()
                break
            except (httpx.TimeoutException, httpx.TransportError, json.JSONDecodeError) as exc:
                last_error = str(exc)
                if index < len(api_keys) - 1:
                    continue
                raise AppError(
                    "GEMINI_EMBEDDING_UNAVAILABLE",
                    "Gemini embedding request failed after trying all configured keys",
                    details=last_error,
                ) from exc
        else:
            raise AppError(
                "GEMINI_EMBEDDING_UNAVAILABLE",
                "Gemini embedding request failed after trying all configured keys",
                details=last_error,
            )
        embedding = data.get("embedding", {}).get("values") if isinstance(data.get("embedding"), dict) else None
        if not isinstance(embedding, list) or not embedding:
            raise AppError("GEMINI_EMBEDDING_INVALID_RESPONSE", "Gemini embedding response did not include values")
        vector = [float(value) for value in embedding]
        if len(vector) > self._gemini_embedding_dimensions:
            vector = vector[: self._gemini_embedding_dimensions]
        if len(vector) != self._gemini_embedding_dimensions:
            raise AppError(
                "GEMINI_EMBEDDING_INVALID_DIMENSIONS",
                "Gemini embedding response dimensions did not match configuration",
                details={"expected": self._gemini_embedding_dimensions, "actual": len(vector)},
            )
        return vector

    def _rotated_gemini_api_keys(self) -> list[str]:
        keys = [key.strip() for key in self._gemini_api_keys if key.strip()]
        if len(keys) <= 1:
            return keys
        with self._gemini_key_lock:
            start = self.__class__._gemini_key_cursor % len(keys)
            self.__class__._gemini_key_cursor += 1
        return keys[start:] + keys[:start]

    async def rerank_windows(self, question: str, windows: list[dict], limit: int) -> list[dict]:
        if len(windows) <= limit:
            return windows
        prompt = _rerank_prompt(question, windows, limit)
        try:
            data = await self._post_json(
                "/chat/completions",
                self._with_thinking({
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
                    "max_tokens": min(self._max_tokens, 1200),
                }),
            )
            parsed = _parse_json_object(_message_text(data))
        except Exception:
            return windows[:limit]
        ranked_ids = [
            str(item.get("video_window_id") or item.get("id") or "")
            for item in _list_of_dicts(parsed.get("ranked_windows"))
        ]
        by_id = {str(window["id"]): window for window in windows}
        ranked = [by_id[window_id] for window_id in ranked_ids if window_id in by_id]
        ranked.extend(window for window in windows if window not in ranked)
        return ranked[:limit]

    async def verify_and_answer_question(self, video_id: str, question: str, windows: list[dict]) -> QuestionAnswer:
        started = perf_counter()
        prompt = _verified_qa_prompt(question, windows)
        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        for window in windows:
            clip_path_value = window.get("local_clip_path")
            if not clip_path_value:
                continue
            clip_path = Path(str(clip_path_value))
            if not clip_path.is_file() or clip_path.stat().st_size > self._max_video_bytes:
                continue
            content.append({"type": "text", "text": f"Video evidence for window_id={window['id']}:"})
            content.append(
                {
                    "type": "video_url",
                    "video_url": {
                        "url": _data_url(clip_path),
                        "fps": self._video_fps,
                    },
                }
            )
        data = await self._post_json(
            "/chat/completions",
            self._with_thinking({
                "model": self.model_name,
                "messages": [{"role": "user", "content": content}],
                "max_tokens": self._max_tokens,
            }),
        )
        parsed = _parse_json_object(_message_text(data))
        evidence = parsed.get("evidence") if isinstance(parsed.get("evidence"), list) else []
        return QuestionAnswer(
            answer=str(parsed.get("answer") or "Indexed evidence is insufficient to answer this question."),
            latency_ms=int((perf_counter() - started) * 1000),
            estimated_cost=0.0,
            evidence=[
                {
                    "video_window_id": str(item.get("video_window_id") or item.get("window_id") or ""),
                    "timestamp": float(item.get("timestamp") or item.get("start_time") or 0),
                    "rationale": str(item.get("rationale") or item.get("reason") or "Seed verified this evidence."),
                }
                for item in evidence
                if isinstance(item, dict) and item.get("matched", True) is not False
            ],
        )

    def _with_thinking(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self._thinking_enabled:
            payload["thinking"] = {"type": "enabled"}
            if self._reasoning_effort:
                payload["reasoning"] = {"effort": self._reasoning_effort}
        else:
            payload["thinking"] = {"type": "disabled"}
        return payload

    async def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        last_error: Exception | None = None
        model_names = self._request_model_names(payload)
        for model_index, model_name in enumerate(model_names):
            request_payload = dict(payload)
            request_payload["model"] = model_name
            for _ in range(2):
                try:
                    async with self._client() as client:
                        response = await client.post(path, json=request_payload)
                    if response.status_code >= 400:
                        last_error = AppError(
                            "SEED_API_ERROR",
                            "Seed API request failed",
                            response.status_code,
                            details=response.text[-2000:],
                        )
                        if response.status_code in {403, 404} and model_index < len(model_names) - 1:
                            break
                        raise last_error
                    data = response.json()
                    if not isinstance(data, dict):
                        raise AppError("SEED_API_INVALID_RESPONSE", "Seed API returned a non-object response")
                    self.model_name = model_name
                    return data
                except (httpx.TimeoutException, httpx.TransportError, json.JSONDecodeError) as exc:
                    last_error = exc
        raise AppError("SEED_API_UNAVAILABLE", "Seed API request failed after retry", details=str(last_error))

    def _request_model_names(self, payload: dict[str, Any]) -> list[str]:
        requested = str(payload.get("model") or self.model_name)
        return _unique_model_names([requested, *self._model_names])


def _analysis_prompt(start_time: float, end_time: float) -> str:
    return f"""
You analyze a short ecommerce video window from {start_time:.3f}s to {end_time:.3f}s.

Goal: build an evidence-grounded ecommerce video index for natural-language QA, SKU timeline,
speech-vs-visual compliance checks, multilingual transcript browsing, OCR search and product tracking.

Rules:
- Produce only facts supported by the attached video window.
- If speech/audio is understandable, transcribe timestamped speech segments verbatim in the source language. Do not summarize speech in English unless the speaker is actually speaking English.
- Use Vietnamese for all non-verbatim generated descriptions, labels, explanations, claims, rationale-like text, product descriptions and scene descriptions.
- Put English only in the "translation" fields. For Vietnamese source speech, "transcript" and speech_segments[].text must stay Vietnamese, while speech_segments[].translation may contain English.
- If speech/audio is not understandable, keep speech_segments empty instead of inventing speech.
- Detect visible UI/OCR text including prices, free shipping, countdown timers, pinned product cards and discount badges.
- Separate visible products from livestream comments. A product mentioned only in chat/comment OCR is not a detected product.
- Do not treat the creator/shop/channel name as a product. Names like HannahOlala, Hannah Olala, or Whoo x Hannah Olala are host/shop/campaign names unless a real product package says that exact product name.
- Still detect creator, KOL, host, shop and channel names as non-product entities with timestamps when they appear in profile UI, OCR, speech, badges or scene context.
- Do not treat platform product shelves/cards/carousels/banners at the bottom of the livestream UI as detected products.
- Bottom product cards are UI metadata only. Put their text in ocr_text with source="bottom_product_card" or "platform_product_card"; do not put them in products or detected_entities as type="product".
- The small active product card near the upper-left/left side of the live video may count as product evidence. Use source="active_live_product_card" or "top_left_product_card" for that card.
- A detected product must be physically visible in the live scene, held by the host, demonstrated, readable on real packaging, or shown in the active upper-left live product card.
- For ecommerce product extraction, prefer real package labels, visible packaging, host demonstrations, and the active upper-left live product card. Do not use bottom product shelf OCR as product evidence.
- Only include a product in products when a brand label or SKU is readable. If the brand/SKU cannot be read, keep it in scene_description or detected_entities as packaging/other, not as a product.
- Use null/unknown if brand, SKU or exact product name is not readable. Do not guess brand names.
- If a product name is generic, mark is_exact_product=false and lower confidence.
- Preserve timestamps relative to the original video, between {start_time:.3f} and {end_time:.3f}.

Return JSON only with this shape:
{{
  "language": "vi|th|id|tl|zh|en|mixed|unknown",
  "transcript": "",
  "speech_segments": [
    {{"start_time": {start_time:.3f}, "end_time": {start_time:.3f}, "speaker": "host|guest|unknown", "text": "", "translation": null, "language": "vi|th|id|tl|zh|en|unknown", "confidence": 0.0}}
  ],
  "translation": null,
  "scene_description": "",
  "visual_evidence": [
    {{"timestamp": {start_time:.3f}, "modality": "visual|ocr|audio", "text": "", "confidence": 0.0}}
  ],
  "ocr_text": [{{"text": "", "timestamp": {start_time:.3f}, "source": "product_label|active_live_product_card|top_left_product_card|price_badge|countdown|chat|bottom_product_card|platform_product_card|ui|other", "confidence": 0.0}}],
  "products": [{{
    "brand": null,
    "product_name": null,
    "sku": null,
    "name": null,
    "category": null,
    "description": "",
    "is_exact_product": false,
    "evidence_source": "visual_label|physical_label|visible_packaging|host_demo|held_product|visual_shape|active_live_product_card|top_left_product_card|bottom_product_card|platform_product_card|comment|unknown",
    "evidence_text": "",
    "timestamp": {start_time:.3f},
    "is_from_comment": false,
    "confidence": 0.0
  }}],
  "actions": [{{"label": "", "confidence": 0.0}}],
  "business_events": [{{"label": "price_mention|discount_mention|free_ship|countdown|call_to_action|product_demo|comparison|other", "text": "", "timestamp": {start_time:.3f}, "confidence": 0.0}}],
  "audio_events": [{{"label": "speech|laugh|order_sound|music_peak|cheer|silence|other", "timestamp": {start_time:.3f}, "text": "", "confidence": 0.0}}],
  "detected_entities": [{{"type": "product|person|brand|price|promotion|host|kol|creator|shop|channel|platform|packaging|other", "name": "", "evidence_source": "visual_label|physical_label|visible_packaging|host_demo|held_product|visual_shape|profile_ui|ui_ocr|active_live_product_card|top_left_product_card|speech|bottom_product_card|platform_product_card|comment|unknown", "evidence_text": "", "is_from_comment": false, "confidence": 0.0}}],
  "claims": [{{"claim_text": "", "timestamp": {start_time:.3f}, "speaker": null}}],
  "energy_score": 0.0,
  "emotion": null
}}

Do not include markdown.
""".strip()


def _rerank_prompt(question: str, windows: list[dict], limit: int) -> str:
    compact_windows = [
        _trusted_qa_window_metadata(question, window)
        for window in windows
    ]
    return f"""
Rerank ecommerce video chunks for the user's question.
Prioritize chunks with direct visual/product-card evidence. Penalize chunks where the match only appears in livestream comments.
For brand/product questions, ignore bottom product shelves/cards, platform shopping UI, Shopee banners, and chat/comment OCR unless the user explicitly asks about them.
Return reasons in the same language as the user's question.

Question: {question}
Candidate chunks:
{json.dumps(compact_windows, ensure_ascii=False)}

Return JSON only:
{{
  "ranked_windows": [
    {{"video_window_id": "", "score": 0.0, "reason": ""}}
  ]
}}

Return at most {limit} ranked_windows.
""".strip()


def _verified_qa_prompt(question: str, windows: list[dict]) -> str:
    compact_windows = []
    for window in windows:
        compact = _trusted_qa_window_metadata(question, window)
        compact["has_video_evidence"] = bool(window.get("local_clip_path"))
        compact_windows.append(compact)
    return f"""
Answer the user's question using only the candidate video chunks and attached video evidence.

Verification rules:
- Answer in the same language as the user's question.
- Confirm the answer against the attached chunk videos when available.
- Do not treat livestream chat/comment OCR as product evidence unless the user asks about comments.
- Do not use bottom product shelves/cards, platform shopping UI, Shopee banners, or pinned bottom cards as brand/product evidence unless the user asks about those UI elements.
- For brand/product list questions, include only brands/products supported by speech, readable physical label/package, host demonstration, or the active upper-left/left live product card.
- If a brand or exact product label is not readable, say the indexed evidence is insufficient for that exact brand/name.
- Include timestamp evidence from the original video.
- Keep every evidence rationale in the same language as the user's question.
- GROUNDING REQUIREMENT: every affirmative answer must be supported by at least 2 modalities from {{audio/transcript, visual/scene_description, OCR text}}. If fewer than 2 modalities corroborate the claim, set the answer to "not found in this video" and explain why evidence is insufficient.

Question: {question}

Candidate metadata:
{json.dumps(compact_windows, ensure_ascii=False)}

Return JSON only:
{{
  "answer": "",
  "evidence": [
    {{"video_window_id": "", "timestamp": 0.0, "matched": true, "rationale": ""}}
  ]
}}
""".strip()


def _trusted_qa_window_metadata(question: str, window: dict) -> dict:
    trusted_ocr = _trusted_qa_items(question, window.get("ocr_text") or [])
    trusted_entities = _trusted_qa_items(question, window.get("detected_entities") or [])
    index_text = "\n".join(
        str(value)
        for value in [
            window.get("transcript"),
            window.get("scene_description"),
            " ".join(str(item) for item in trusted_ocr),
            " ".join(str(item) for item in trusted_entities),
        ]
        if value
    )
    return {
        "id": window.get("id"),
        "start_time": window.get("start_time"),
        "end_time": window.get("end_time"),
        "index_text": index_text,
        "scene_description": window.get("scene_description"),
        "trusted_ocr_text": trusted_ocr,
        "trusted_detected_entities": trusted_entities,
        "chunk_metadata": window.get("chunk_metadata"),
    }


def _trusted_qa_items(question: str, items: list[dict]) -> list[dict]:
    wants_ui_or_comments = _question_wants_ui_or_comment_evidence(question)
    trusted: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if wants_ui_or_comments:
            trusted.append(item)
            continue
        source = str(item.get("evidence_source") or item.get("source") or "").lower()
        if item.get("is_from_comment") is True:
            continue
        if _is_platform_product_ui_source(source, item):
            continue
        if _is_noisy_qa_product_item(item):
            continue
        trusted.append(item)
    return trusted


def _is_noisy_qa_product_item(item: dict) -> bool:
    item_type = str(item.get("type") or "").lower()
    source = str(item.get("evidence_source") or item.get("source") or "").lower()
    if item_type not in {"product", "brand", "price", "promotion"} and "product_card" not in source:
        return False
    text = " ".join(
        str(item.get(key) or "")
        for key in ("name", "brand", "product_name", "text", "evidence_text", "description")
    )
    return _is_non_product_name(text, item)


def _question_wants_ui_or_comment_evidence(question: str) -> bool:
    normalized = question.lower()
    markers = {
        "comment",
        "comments",
        "chat",
        "binh luan",
        "bình luận",
        "nguoi xem",
        "người xem",
        "san pham phia duoi",
        "sản phẩm phía dưới",
        "khung duoi",
        "khung dưới",
        "bottom",
        "shopee",
        "gio hang",
        "giỏ hàng",
    }
    return any(marker in normalized for marker in markers)


def _qa_prompt(question: str, windows: list[dict]) -> str:
    return f"""
Answer the user's question using only the indexed video windows below.
If evidence is insufficient, say that the indexed evidence is insufficient.
Answer and write evidence rationale in the same language as the user's question.

Question: {question}

Windows JSON:
{json.dumps(windows, ensure_ascii=False)}

Return JSON only:
{{
  "answer": "",
  "evidence": [
    {{"video_window_id": "", "timestamp": 0.0, "rationale": ""}}
  ]
}}
""".strip()


def _verification_prompt(claim_text: str, evidence: list[dict]) -> str:
    return f"""
Check whether this ecommerce claim is supported by the indexed multimodal evidence and attached video clips.

Rules:
- Compare the spoken/text claim with visible packaging, product cards, certificates, OCR and scene content.
- If the claim requires proof within a nearby time window, use the attached clip and timestamp metadata.
- Return inconsistent when speech asserts something that the visual evidence contradicts.
- Return unclear when visual/audio evidence is insufficient.

Claim: {claim_text}
Evidence JSON:
{json.dumps(evidence, ensure_ascii=False)}

Return JSON only:
{{
  "verdict": "consistent|inconsistent|unclear",
  "confidence": 0.0,
  "explanation": "",
  "evidence_frame_ids": []
}}
""".strip()


def _product_consolidation_prompt(candidates: list[dict]) -> str:
    return f"""
You consolidate product candidates extracted from an ecommerce video.

Task:
- Merge duplicate mentions of the same product across chunks.
- Reject generic product labels unless no better exact label exists.
- Reject platform product shelves/cards/carousels/pinned product cards at the bottom of the livestream UI.
- Accept the active upper-left/left live product card as product evidence when it shows a product image/title/price for the current live item.
- Reject host/shop/channel/campaign names as product names, including HannahOlala, Hannah Olala, and Whoo x Hannah Olala.
- Reject product candidates without a readable brand or SKU. Do not keep generic objects such as "skincare serum", "liquid bottle", "unknown toner", or "sunscreen" in the product list.
- Prefer exact brand + product names from real package labels, visible packaging, host-held products, active upper-left live product cards, or clear speech tied to the visible product.
- Do not invent brands, SKUs or product names.
- Keep product occurrences with timestamps and evidence text.
- Mark occurrence_type as visual, ocr or spoken.

Candidate JSON:
{json.dumps(candidates, ensure_ascii=False)}

Return JSON only:
{{
  "products": [
    {{
      "canonical_name": "",
      "brand": null,
      "product_name": null,
      "sku": null,
      "description": "",
      "confidence": 0.0,
      "evidence_summary": "",
      "occurrences": [
        {{"video_window_id": "", "timestamp": 0.0, "occurrence_type": "visual|ocr|spoken", "confidence": 0.0, "evidence_text": ""}}
      ]
    }}
  ]
}}
""".strip()


def _product_candidates_from_windows(windows: list[dict]) -> list[dict]:
    candidates: list[dict] = []
    for window in windows:
        window_id = str(window.get("id") or "")
        if not window_id:
            continue
        window_start = _float_value(window.get("start_time"), default=0.0)
        window_end = _float_value(window.get("end_time"), default=window_start)
        ocr_text = window.get("ocr_text") if isinstance(window.get("ocr_text"), list) else []
        for entity in window.get("detected_entities") or []:
            if not isinstance(entity, dict) or entity.get("type") != "product":
                continue
            if entity.get("is_from_comment") is True:
                continue
            evidence_source = str(entity.get("evidence_source") or "").lower()
            if _is_platform_product_ui_source(evidence_source, entity):
                continue
            if evidence_source and evidence_source not in PHYSICAL_PRODUCT_SOURCES:
                continue
            confidence = _bounded_float(entity.get("confidence"), default=0.0)
            if confidence < 0.45:
                continue
            name = _product_display_name(entity)
            if not name:
                continue
            if _is_non_product_name(name, entity):
                continue
            if not _has_readable_product_identity(entity, name):
                continue
            timestamp = min(window_end, max(window_start, _float_value(entity.get("timestamp"), default=window_start)))
            candidates.append(
                {
                    "video_window_id": window_id,
                    "start_time": window_start,
                    "end_time": window_end,
                    "timestamp": timestamp,
                    "name": name,
                    "brand": entity.get("brand"),
                    "product_name": entity.get("product_name"),
                    "sku": entity.get("sku"),
                    "category": entity.get("category"),
                    "description": entity.get("description"),
                    "is_exact_product": bool(entity.get("is_exact_product")),
                    "evidence_source": entity.get("evidence_source"),
                    "evidence_text": entity.get("evidence_text"),
                    "confidence": confidence,
                    "scene_description": window.get("scene_description"),
                    "nearby_ocr": ocr_text[:12],
                }
            )
    return candidates


def _products_from_consolidation(parsed: dict[str, Any], candidates: list[dict]) -> list[dict]:
    candidate_window_ids = {str(item.get("video_window_id")) for item in candidates}
    products: list[dict] = []
    seen: set[str] = set()
    for raw in _list_of_dicts(parsed.get("products")):
        name = str(raw.get("canonical_name") or raw.get("name") or "").strip()
        confidence = _bounded_float(raw.get("confidence"), default=0.0)
        if (
            not name
            or _is_generic_product_name(name)
            or _is_non_product_name(name, raw)
            or not _has_readable_product_identity(raw, name)
            or confidence < 0.6
        ):
            continue
        normalized = _normalize_product_name(name)
        if normalized in seen:
            continue
        occurrences = []
        for occurrence in _list_of_dicts(raw.get("occurrences")):
            window_id = str(occurrence.get("video_window_id") or "")
            if window_id not in candidate_window_ids:
                continue
            if _is_platform_product_ui_source(occurrence.get("occurrence_type"), occurrence):
                continue
            occurrences.append(
                {
                    "video_window_id": window_id,
                    "timestamp": _float_value(occurrence.get("timestamp"), default=0.0),
                    "occurrence_type": _normalize_occurrence_type(occurrence.get("occurrence_type")),
                    "confidence": _bounded_float(occurrence.get("confidence"), default=confidence),
                    "evidence_text": str(occurrence.get("evidence_text") or raw.get("evidence_summary") or ""),
                }
            )
        if not occurrences:
            continue
        seen.add(normalized)
        sku = str(raw.get("sku") or "").strip() or f"SEED-{hashlib.sha1(normalized.encode('utf-8')).hexdigest()[:8].upper()}"
        products.append(
            {
                "sku": sku[:128],
                "name": name[:255],
                "description": str(raw.get("description") or raw.get("evidence_summary") or "Product verified from video evidence."),
                "confidence": confidence,
                "timestamp": occurrences[0]["timestamp"],
                "video_window_id": occurrences[0]["video_window_id"],
                "occurrences": occurrences,
                "metadata": {
                    "brand": raw.get("brand"),
                    "product_name": raw.get("product_name"),
                    "evidence_summary": raw.get("evidence_summary"),
                    "source": "seed_product_consolidation",
                },
            }
        )
    return products


def _fallback_products_from_candidates(candidates: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for candidate in candidates:
        if _is_platform_product_ui_source(candidate.get("evidence_source"), candidate):
            continue
        name = str(candidate.get("name") or "").strip()
        if (
            not name
            or _is_generic_product_name(name)
            or _is_non_product_name(name, candidate)
            or not _has_readable_product_identity(candidate, name)
        ):
            continue
        confidence = _bounded_float(candidate.get("confidence"), default=0.0)
        if confidence < 0.7:
            continue
        normalized = _normalize_product_name(name)
        item = grouped.setdefault(
            normalized,
            {
                "sku": f"SEED-{hashlib.sha1(normalized.encode('utf-8')).hexdigest()[:8].upper()}",
                "name": name[:255],
                "description": str(candidate.get("description") or candidate.get("category") or "Product detected by Seed 2.0."),
                "confidence": confidence,
                "timestamp": _float_value(candidate.get("timestamp"), default=0.0),
                "video_window_id": str(candidate.get("video_window_id")),
                "occurrences": [],
                "metadata": {
                    "brand": candidate.get("brand"),
                    "product_name": candidate.get("product_name"),
                    "source": "seed_product_fallback",
                },
            },
        )
        item["confidence"] = max(item["confidence"], confidence)
        item["occurrences"].append(
            {
                "video_window_id": str(candidate.get("video_window_id")),
                "timestamp": _float_value(candidate.get("timestamp"), default=0.0),
                "occurrence_type": _normalize_occurrence_type(candidate.get("evidence_source")),
                "confidence": confidence,
                "evidence_text": str(candidate.get("evidence_text") or ""),
            }
        )
    return list(grouped.values())


def _data_url(path) -> str:
    mime_type = mimetypes.guess_type(str(path))[0] or "video/mp4"
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{payload}"


def _message_text(data: dict[str, Any]) -> str:
    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "\n".join(str(item.get("text") or item) for item in content)
    raise AppError("SEED_API_INVALID_RESPONSE", "Seed response did not include message content")


def _parse_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    fenced = JSON_FENCE_PATTERN.search(text)
    if fenced:
        text = fenced.group(1).strip()
    candidates = [text]
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        extracted = text[start : end + 1]
        if extracted != text:
            candidates.append(extracted)

    errors: list[str] = []
    for candidate in candidates:
        try:
            data = _json_loads_with_repairs(candidate)
            break
        except json.JSONDecodeError as exc:
            errors.append(f"line {exc.lineno} column {exc.colno}: {exc.msg}")
    else:
        raise AppError(
            "SEED_JSON_PARSE_FAILED",
            "Seed response was not valid JSON",
            details={"errors": errors, "response": text[:2000]},
        )
    if not isinstance(data, dict):
        raise AppError("SEED_JSON_PARSE_FAILED", "Seed JSON response must be an object")
    return data


def _json_loads_with_repairs(text: str) -> Any:
    variants = [text]
    without_trailing_commas = _remove_json_trailing_commas(text)
    if without_trailing_commas != text:
        variants.append(without_trailing_commas)
    with_decimal_zeroes = _prefix_json_leading_decimal_zeroes(text)
    if with_decimal_zeroes != text:
        variants.append(with_decimal_zeroes)
        without_trailing_commas = _remove_json_trailing_commas(with_decimal_zeroes)
        if without_trailing_commas != with_decimal_zeroes:
            variants.append(without_trailing_commas)

    for variant in list(variants):
        quoted_keys = _quote_json_bare_object_keys(variant)
        if quoted_keys != variant:
            variants.append(quoted_keys)
            without_trailing_commas = _remove_json_trailing_commas(quoted_keys)
            if without_trailing_commas != quoted_keys:
                variants.append(without_trailing_commas)
            with_decimal_zeroes = _prefix_json_leading_decimal_zeroes(quoted_keys)
            if with_decimal_zeroes != quoted_keys:
                variants.append(with_decimal_zeroes)
                without_trailing_commas = _remove_json_trailing_commas(with_decimal_zeroes)
                if without_trailing_commas != with_decimal_zeroes:
                    variants.append(without_trailing_commas)
    for variant in list(variants):
        with_key_colons = _insert_missing_json_key_colons(variant)
        if with_key_colons != variant:
            variants.append(with_key_colons)
            without_trailing_commas = _remove_json_trailing_commas(with_key_colons)
            if without_trailing_commas != with_key_colons:
                variants.append(without_trailing_commas)
            with_decimal_zeroes = _prefix_json_leading_decimal_zeroes(with_key_colons)
            if with_decimal_zeroes != with_key_colons:
                variants.append(with_decimal_zeroes)
                without_trailing_commas = _remove_json_trailing_commas(with_decimal_zeroes)
                if without_trailing_commas != with_decimal_zeroes:
                    variants.append(without_trailing_commas)

    last_error: json.JSONDecodeError | None = None
    for variant in variants:
        try:
            return json.loads(variant)
        except json.JSONDecodeError as exc:
            last_error = exc
    if last_error:
        raise last_error
    return json.loads(text)


def _remove_json_trailing_commas(text: str) -> str:
    result: list[str] = []
    in_string = False
    escape = False
    index = 0
    while index < len(text):
        char = text[index]
        if in_string:
            result.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            result.append(char)
            index += 1
            continue
        if char == ",":
            next_index = index + 1
            while next_index < len(text) and text[next_index].isspace():
                next_index += 1
            if next_index < len(text) and text[next_index] in "}]":
                index += 1
                continue
        result.append(char)
        index += 1
    return "".join(result)


def _quote_json_bare_object_keys(text: str) -> str:
    result: list[str] = []
    in_string = False
    escape = False
    index = 0
    while index < len(text):
        char = text[index]
        if in_string:
            result.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            result.append(char)
            index += 1
            continue
        if char in "{,":
            result.append(char)
            index += 1
            while index < len(text) and text[index].isspace():
                result.append(text[index])
                index += 1
            key_start = index
            if key_start < len(text) and (text[key_start].isalpha() or text[key_start] == "_"):
                index += 1
                while index < len(text) and (text[index].isalnum() or text[index] in "_-$"):
                    index += 1
                key_end = index
                whitespace_start = index
                while index < len(text) and text[index].isspace():
                    index += 1
                if index < len(text) and text[index] == ":":
                    key = text[key_start:key_end]
                    whitespace = text[whitespace_start:index]
                    result.append(f'"{key}"{whitespace}:')
                    index += 1
                    continue
                if index < len(text) and _looks_like_json_value_start(text[index]):
                    key = text[key_start:key_end]
                    whitespace = text[whitespace_start:index]
                    result.append(f'"{key}":{whitespace}')
                    continue
                result.append(text[key_start:index])
                continue
            continue
        result.append(char)
        index += 1
    return "".join(result)


def _insert_missing_json_key_colons(text: str) -> str:
    result: list[str] = []
    in_string = False
    escape = False
    index = 0
    while index < len(text):
        char = text[index]
        if in_string:
            result.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            result.append(char)
            index += 1
            continue
        if char in "{,":
            result.append(char)
            index += 1
            whitespace_start = index
            while index < len(text) and text[index].isspace():
                index += 1
            if index >= len(text) or text[index] != '"':
                result.append(text[whitespace_start:index])
                continue
            key_start = index
            index = _json_string_end(text, key_start)
            if index <= key_start:
                result.append(text[whitespace_start:])
                break
            key_end = index
            while index < len(text) and text[index].isspace():
                index += 1
            if index < len(text) and text[index] not in ":,}]" and _looks_like_json_value_start(text[index]):
                result.append(text[whitespace_start:key_end])
                result.append(":")
                result.append(text[key_end:index])
                continue
            result.append(text[whitespace_start:index])
            continue
        result.append(char)
        index += 1
    return "".join(result)


def _prefix_json_leading_decimal_zeroes(text: str) -> str:
    result: list[str] = []
    in_string = False
    escape = False
    index = 0
    while index < len(text):
        char = text[index]
        if in_string:
            result.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            result.append(char)
            index += 1
            continue
        if char == "." and index + 1 < len(text) and text[index + 1].isdigit() and _previous_json_value_boundary(text, index):
            result.append("0")
        elif (
            char == "-"
            and index + 2 < len(text)
            and text[index + 1] == "."
            and text[index + 2].isdigit()
            and _previous_json_value_boundary(text, index)
        ):
            result.append("-0")
            index += 1
            continue
        result.append(char)
        index += 1
    return "".join(result)


def _previous_json_value_boundary(text: str, index: int) -> bool:
    previous = index - 1
    while previous >= 0 and text[previous].isspace():
        previous -= 1
    return previous < 0 or text[previous] in ":[,"


def _json_string_end(text: str, start: int) -> int:
    index = start + 1
    escape = False
    while index < len(text):
        char = text[index]
        if escape:
            escape = False
        elif char == "\\":
            escape = True
        elif char == '"':
            return index + 1
        index += 1
    return start


def _looks_like_json_value_start(char: str) -> bool:
    return char == '"' or char in "{[.-0123456789tfn"


def _fallback_analysis_from_unparseable_response(_text: str, start_time: float, end_time: float) -> VideoWindowAnalysis:
    return VideoWindowAnalysis(
        transcript="",
        translation=None,
        language="unknown",
        speech_segments=[],
        scene_description="Không thể phân tích phản hồi JSON từ mô hình cho đoạn video này.",
        ocr_text=[],
        visual_evidence=[
            {
                "timestamp": start_time,
                "modality": "visual",
                "text": "Model response was not valid JSON; window kept with fallback metadata.",
                "confidence": 0.0,
            }
        ],
        audio_events=[],
        detected_entities=[
            {
                "type": "analysis_error",
                "name": "seed_json_parse_failed",
                "timestamp": start_time,
                "evidence_source": "model_response",
                "evidence_text": "",
                "confidence": 0.0,
            }
        ],
        energy_score=0.0,
        emotion=None,
        claims=[],
    )


def _analysis_from_json(data: dict[str, Any], start_time: float, end_time: float) -> VideoWindowAnalysis:
    speech_segments = _timestamped_items(
        _list_of_dicts(data.get("speech_segments") or data.get("transcript_segments")),
        start_time,
        end_time,
    )
    transcript = str(data.get("transcript") or "").strip()
    if not transcript and speech_segments:
        transcript = " ".join(str(item.get("text") or "").strip() for item in speech_segments if item.get("text")).strip()

    visual_evidence = _timestamped_items(_list_of_dicts(data.get("visual_evidence")), start_time, end_time)
    ocr_text = _timestamped_items(_list_of_dicts(data.get("ocr_text")), start_time, end_time)
    audio_events = _timestamped_items(_list_of_dicts(data.get("audio_events")), start_time, end_time)

    detected_entities = _list_of_dicts(data.get("detected_entities"))
    for product in _list_of_dicts(data.get("products")):
        name = _product_display_name(product)
        if name:
            detected_entities.append(
                {
                    "type": "product",
                    "name": name,
                    "brand": product.get("brand") if isinstance(product.get("brand"), str) else None,
                    "product_name": product.get("product_name") if isinstance(product.get("product_name"), str) else None,
                    "sku": product.get("sku") if isinstance(product.get("sku"), str) else None,
                    "category": product.get("category") if isinstance(product.get("category"), str) else None,
                    "description": str(product.get("description") or ""),
                    "is_exact_product": bool(product.get("is_exact_product")),
                    "evidence_source": str(product.get("evidence_source") or "unknown"),
                    "evidence_text": str(product.get("evidence_text") or ""),
                    "is_from_comment": bool(product.get("is_from_comment")),
                    "confidence": _bounded_float(product.get("confidence"), default=0.75),
                    "timestamp": min(end_time, max(start_time, _float_value(product.get("timestamp"), default=start_time))),
                }
            )
    for action in _list_of_dicts(data.get("actions")):
        detected_entities.append({"type": "action", **action})
    for event in _list_of_dicts(data.get("business_events")):
        detected_entities.append({"type": "business_event", **event})

    return VideoWindowAnalysis(
        transcript=transcript,
        translation=data.get("translation") if isinstance(data.get("translation"), str) else None,
        language=str(data.get("language") or "unknown"),
        speech_segments=speech_segments,
        scene_description=str(data.get("scene_description") or ""),
        ocr_text=ocr_text,
        visual_evidence=visual_evidence,
        audio_events=audio_events,
        detected_entities=_timestamped_items(detected_entities, start_time, end_time),
        energy_score=_bounded_float(data.get("energy_score"), default=0.0),
        emotion=str(data.get("emotion")) if data.get("emotion") else None,
        claims=[
            {
                "claim_text": str(item.get("claim_text") or ""),
                "timestamp": min(end_time, max(start_time, _float_value(item.get("timestamp"), default=start_time))),
                "speaker": item.get("speaker") if isinstance(item.get("speaker"), str) else None,
            }
            for item in _list_of_dicts(data.get("claims"))
            if item.get("claim_text")
        ],
    )


def _timestamped_items(items: list[dict], start_time: float, end_time: float) -> list[dict]:
    normalized: list[dict] = []
    for item in items:
        copy = dict(item)
        if "timestamp" in copy:
            copy["timestamp"] = min(end_time, max(start_time, _float_value(copy.get("timestamp"), default=start_time)))
        if "start_time" in copy:
            copy["start_time"] = min(end_time, max(start_time, _float_value(copy.get("start_time"), default=start_time)))
        if "end_time" in copy:
            copy["end_time"] = min(end_time, max(start_time, _float_value(copy.get("end_time"), default=copy.get("start_time") or start_time)))
        normalized.append(copy)
    return normalized


def _list_of_dicts(value: Any) -> list[dict]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _bounded_float(value: Any, *, default: float) -> float:
    number = _float_value(value, default=default)
    return max(0.0, min(1.0, number))


def _float_value(value: Any, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _verdict(value: Any) -> Verdict:
    try:
        return Verdict(str(value))
    except ValueError:
        return Verdict.unclear


def _product_display_name(entity: dict) -> str:
    brand = str(entity.get("brand") or "").strip()
    product_name = str(entity.get("product_name") or "").strip()
    name = str(entity.get("name") or "").strip()
    if brand and product_name and brand.lower() not in product_name.lower():
        return f"{brand} {product_name}".strip()
    return product_name or name


def _is_generic_product_name(name: str) -> bool:
    normalized = re.sub(r"\s+", " ", name.strip().lower())
    generic_names = {
        "skincare",
        "skincare product",
        "skincare products",
        "skincare serum",
        "facial serum",
        "facial skincare serum",
        "skincare serums",
        "skincare toner",
        "toner",
        "serum",
        "lipstick",
        "facial spray serum",
        "spray serum",
        "blue facial serum",
        "purple facial serum",
        "assorted skincare products",
        "skincare collection",
        "skincare serum set",
        "skincare serum/toner",
        "skincare toner/serum bottle",
        "liquid skincare product",
        "liquid skincare bottle",
        "liquid skincare bottle (toner/micellar water)",
        "small liquid skincare bottle",
        "makeup remover water duo",
        "nước tẩy trang dung tích lớn",
        "bộ đôi nước tẩy trang",
        "bộ serum glycolic",
        "discounted skincare product",
        "unknown skincare toner",
        "unknown lip tint",
        "sunscreen",
        "kem chống nắng",
        "acne serum",
        "facial acne serum",
        "blue-capped facial serum",
        "purple-capped facial serum",
        "skincare serum dropper bottle",
        "skincare serum (blue cap)",
        "skincare serum (purple cap)",
        "skincare serum (purple variant)",
        "serum dưỡng da",
        "serum (skincare serum)",
    }
    return normalized in generic_names


def _is_non_product_name(name: str, entity: dict | None = None) -> bool:
    haystack = _normalize_product_name(name)
    if entity:
        haystack = " ".join(
            [
                haystack,
                _normalize_product_name(str(entity.get("brand") or "")),
                _normalize_product_name(str(entity.get("product_name") or "")),
                _normalize_product_name(str(entity.get("evidence_text") or "")),
            ]
        )
    return any(pattern in haystack for pattern in NON_PRODUCT_NAME_PATTERNS)


def _has_readable_product_identity(entity: dict, name: str) -> bool:
    brand = _normalize_product_name(str(entity.get("brand") or ""))
    product_name = _normalize_product_name(str(entity.get("product_name") or ""))
    sku = _normalize_product_name(str(entity.get("sku") or ""))
    evidence_text = _normalize_product_name(str(entity.get("evidence_text") or entity.get("evidence_summary") or ""))
    normalized_name = _normalize_product_name(name)

    if brand and brand not in {"unknown", "null", "none", "n/a"} and not _is_generic_product_name(brand):
        return True
    if sku and sku not in {"unknown", "null", "none", "n/a"}:
        return True
    combined = " ".join([normalized_name, product_name, evidence_text])
    if any(token in combined for token in {"l'oreal", "loreal", "la roche", "posay", "paula", "whoo", "cocoon"}):
        return True
    return False


def _normalize_product_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def _normalize_occurrence_type(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"spoken", "speech", "audio"}:
        return "spoken"
    if normalized in {"ocr", "visual_label", "physical_label", "visible_packaging", "label", "price_badge"}:
        return "ocr"
    return "visual"


def _is_platform_product_ui_source(source: Any, item: dict | None = None) -> bool:
    normalized = str(source or "").strip().lower()
    if normalized in ACTIVE_LIVE_PRODUCT_CARD_SOURCES:
        return False
    if normalized in PLATFORM_PRODUCT_UI_SOURCES:
        return True
    if not item:
        return False
    text = " ".join(
        str(item.get(key) or "")
        for key in ("source", "evidence_source", "evidence_text", "description", "name")
    ).lower()
    if any(marker in text for marker in {"active live product", "top left product", "upper-left product", "left product card"}):
        return False
    ui_markers = {
        "bottom product",
        "product shelf",
        "shopping shelf",
        "pinned product",
        "platform product",
        "yellow cart",
        "cart icon",
        "bottom card",
        "carousel",
    }
    return any(marker in text for marker in ui_markers)


def _unique_model_names(model_names: list[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for model_name in model_names:
        normalized = str(model_name or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique.append(normalized)
    return unique


def _gemini_model_resource(model: str) -> str:
    model = model.strip()
    return model if model.startswith("models/") else f"models/{model}"


def _gemini_task_type(task_type: str) -> str:
    normalized = task_type.strip().upper()
    allowed = {
        "RETRIEVAL_QUERY",
        "RETRIEVAL_DOCUMENT",
        "SEMANTIC_SIMILARITY",
        "CLASSIFICATION",
        "CLUSTERING",
        "QUESTION_ANSWERING",
        "FACT_VERIFICATION",
        "CODE_RETRIEVAL_QUERY",
    }
    return normalized if normalized in allowed else "RETRIEVAL_DOCUMENT"
