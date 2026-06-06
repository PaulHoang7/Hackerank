---
name: claim-visual-verification
description: Use when implementing claim-vs-visual verification, compliance checking, or temporal retrieval — detect a spoken claim, fetch the frames around it, and have the model judge whether the visual evidence is consistent; run market compliance rules (authenticity, discount, free-ship, FTC-style disclosure) with frame-cited violations; and answer temporal "X while Y" queries. Stages 6b/6c. Read 00-overview first.
---

# claim-visual-verification · Stage 6b/6c (Verify · Compliance · Temporal)

Check whether what was *said* matches what was *shown*, and answer compliance/temporal queries — all with paired audio + frame evidence.

## When to use
"Host said X — is the visual consistent?"; compliance audits; "find every moment X while Y is visible".

## Core 1 — Claim-vs-Visual (6b)
1. Locate the transcript claim "X" (with timestamp).
2. Fetch frames at that timestamp **+ the next 5s** (claims are often supported shortly after).
3. Ask the model (`reasoning_effort: medium/high`): *"Does the visual prove X? Is the claim negated?"* → `is_verified` + frame proof + reason.

## Core 2 — Compliance (6c) — HYBRID rule + model (locked)
- **Rules find candidates (cheap, high recall):** transcript contains authenticity ("chính hãng"/"authentic"/"official"), discount ("giảm giá"/"sale"), free-ship ("free ship"/"miễn phí vận chuyển"), etc.
- **Model judges (accurate):** for each candidate, ask the model to check the relevant frames — *certificate visible? price/% overlay present? FREE-SHIP overlay shown ≥3s? is the phrase negated?* This handles paraphrase, code-switching, negation, and OCR misses (absence is unreliable via keyword alone).
- Output `not_supported | warning | ok` with paired audio+frame evidence.

Example rules: authenticity claim with **no certificate within 5s → violation**; discount claim with **no price/% overlay → warning**; free-ship claim with **no FREE-SHIP overlay → warning**.

## Core 3 — Temporal retrieval (6c)
"Find every moment X while Y is visible" → use `retrieval-index` **exhaustive mode**, then **intersect timelines** on the time axis (e.g., business_event=price_mention ∩ entity sku_27 visible). Return all matches ranked by visibility — never top-k.

## Response shape
```json
{ "claim": "Host says the product is authentic", "result": "not_supported",
  "reason": "Says 'chính hãng' but no certificate/document visible within 5s.",
  "evidence": [{ "start_time": 120, "end_time": 125, "thumbnail_path": "...",
    "transcript": "...", "ocr": [], "visual_description": "Host holds product, no certificate visible" }] }
```

## Gotchas / locked decisions
- **Never decide compliance on keyword presence/absence alone** — the model's visual judgment + negation check is the accuracy source (judged on held-out cases).
- Use the model's visual check for *presence/absence* of certificates/overlays, not OCR-keyword absence.
- Temporal/compliance = exhaustive, not top-k.

## Definition of done
Verifications return `is_verified`/`result` + paired audio+frame proof; compliance handles negation & code-switching; temporal queries return complete intersected sets.
