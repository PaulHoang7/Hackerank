---
name: retrieval-index
description: Use when assembling the final per-window context (retrieval_text), validating records against the schema, embedding for semantic search, populating the vector store, and serving retrieval at query time (hybrid keyword + vector + metadata filter, with neighbor expansion and point-lookup vs exhaustive modes). Stage 5 plus the retrieval used by Stage 6. Read 00-overview first.
---

# retrieval-index · Stage 5 + Retrieval Layer

Turns the enriched windows into a validated, searchable index, and provides the retrieval primitives the answering skills consume. This is the boundary between indexing and serving.

## When to use
After audio + visual + entity stages (to build the index), and whenever a query needs windows retrieved.

## Inputs → Outputs
- **In (build):** enriched windows + entities + occurrences.
- **Out (build):** validated canonical records (source of truth) + a vector store of embeddings; aggregated cost/latency.
- **In (query):** a question (+ optional entity/time/event filters). **Out:** ranked windows with neighbors.

## Build steps (Stage 5)
1. **retrieval_text** — concatenate `transcript_en` + OCR + `visual_description` + entity names + actions + business_events. Include `text_en` so vi/en queries both match.
2. **Validate** every record against the canonical schema (Pydantic) → reject malformed model output (anti-hallucination gate).
3. **Embed** `retrieval_text` with a **multilingual** embedding model → push vectors (with metadata: entity ids, business_events, speaker, times) to the **vector store**.
4. **Persist** canonical records (source of truth) and aggregate `_meta` cost/latency to video level; set `status="indexed"`.

## Retrieval steps (for Stage 6)
1. **Resolve** entity references in the query → `entity_id` (via entity-sku-timeline).
2. **Hybrid search** — keyword + vector + **metadata filter**, fused.
3. **Two modes (locked):**
   - **Point lookup** (typical Q&A): top-k.
   - **Exhaustive** ("find EVERY moment X / compliance / temporal"): **full metadata-filter sweep**, not top-k (top-k under-recalls).
4. **Neighbor expansion** — include prev/next window for context continuity.

## Gotchas / locked decisions
- JSON/DB records are the **control surface** (auditable, groundable); the vector store is only a speed layer.
- Never load the whole video into context at query time — RAG keeps context bounded by design.
- Exhaustive vs point-lookup is a real correctness fork — pick per query type.

## Definition of done
`status=indexed`; multilingual semantic + keyword + filter search returns correct windows with neighbors; exhaustive sweeps return complete sets; cost/latency totals available.
