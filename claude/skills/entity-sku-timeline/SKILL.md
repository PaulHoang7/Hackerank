---
name: entity-sku-timeline
description: Use when turning raw per-window product/person mentions into canonical entities with stable ids, linking the same entity across windows and across languages (Re-ID + multilingual aliases), building the occurrence inverted index, and serving the per-SKU timeline (shown/mentioned/demoed/priced/compared). Stages 4 and 6d. Read 00-overview first.
---

# entity-sku-timeline · Stage 4 + 6d (Entity Resolution & SKU Timeline)

The "gather scattered windows" brain. Converts `products_raw` free strings into **canonical `entity_id`s** anchored on **visual identity + catalog**, so a product is one object with a timeline that spans cuts and languages.

## When to use
After visual indexing, to canonicalize entities and build/serve product timelines.

## Inputs → Outputs
- **In:** all per-window `products_raw` + crop embeddings + OCR names + dialogue mentions; catalog image embeddings (if a context kit exists).
- **Out:** `entities[]` registry + `occurrences{}` inverted index; per-SKU timeline queries.

## Steps
1. **Canonicalize**
   - **With catalog:** match each detection's crop embedding + OCR/name against catalog → assign stable `sku_id`. Use the model (seed-omni-reasoning) to adjudicate borderline matches.
   - **Without catalog:** agglomerative cluster on visual embeddings (+ name similarity) → synthetic `entity_id`.
2. **Re-ID across cuts/reframes** — same visual embedding ⇒ same entity even after a camera cut (this is what "across cuts and reframes" requires).
3. **Multilingual aliases** — build `names {vi, en, brand}` per entity; any-language mention links to the same id. **Anchor on visual + id, never on raw transcript strings.**
4. **Occurrence index** — `entity_id → [{window_id, start/end, action, visibility, thumbnail, evidence{visual,ocr,dialogue_lang}}]`. Classify `action`: shown / mentioned / demoed / priced / compared.
5. **Dedup** — merge occurrences within ~1s (from window overlaps).
6. **SKU timeline (6d)** — `GET timeline(entity_id)` = read `occurrences[id]`, ordered, **ranked by visibility**.

## Writes to Index
`windows[].entities[]` (canonical ids), `entities[]` registry, `occurrences{}`.

## Gotchas / locked decisions
- This is what makes *"show every moment of product A"* an **O(1) metadata filter**, language-independent — not a fuzzy semantic search over strings.
- Visual embedding is the strongest, language-agnostic signal; OCR/dialogue are secondary evidence.
- Keep `evidence` per occurrence so answers can cite ≥2 modalities.

## Definition of done
Each product resolves to one stable id; the same product in 3 separate windows (and in vi + en) returns together; SKU timeline returns ordered, visibility-ranked appearances with thumbnails.
