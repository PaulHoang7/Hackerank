"""RAG transparency report — đối chiếu RETRIEVED ↔ ANSWER.

Với mỗi câu hỏi, hiển thị:
  - TRÁI: các chunk (window) mà RAG đã RETRIEVE và đưa vào LLM; chunk được model
    trích dẫn làm bằng chứng được tô sáng ✓.
  - PHẢI: câu trả lời sinh ra + rationale.
=> Bạn nhìn được câu trả lời có bám đúng dữ liệu lấy ra hay không (không bịa).

Câu hỏi lấy từ backend/eval/gold.json (type qa). Sửa file đó để đổi câu hỏi.
Chạy:  backend/.venv/bin/python backend/rag_inspect.py
Mở:    storage/rag_inspect.html
"""
import base64
import html
import json
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import config, qa  # noqa: E402

_cache: dict[str, str] = {}


def thumb_uri(path):
    if not path:
        return ""
    if path in _cache:
        return _cache[path]
    fp = config.STORAGE / path.lstrip("/")
    if not fp.exists():
        return ""
    _cache[path] = "data:image/jpeg;base64," + base64.b64encode(fp.read_bytes()).decode()
    return _cache[path]


def esc(s):
    return html.escape(str(s or ""))


def short(s, n=200):
    return textwrap.shorten((s or "").replace("\n", " "), n)


def t(s):
    s = int(s or 0)
    return f"{s // 60:02d}:{s % 60:02d}"


def chunk_html(w):
    cls = "chunk cited" if w["cited_as_evidence"] else "chunk"
    badge = "★ DÙNG LÀM BẰNG CHỨNG" if w["cited_as_evidence"] else ""
    uri = thumb_uri(w["thumbnail"])
    img = f'<img src="{uri}">' if uri else ""
    ocr = ", ".join(w["ocr"][:6])
    return f"""<div class="{cls}">
      <div class="ch">{img}<div><b>{esc(w['window_id'])} · {t(w['start_time'])}-{t(w['end_time'])}</b>
        <span class="bdg">{badge}</span>
        <div class="ev">events={esc(w['business_events'])} · ent={esc(w['entities'])}</div></div></div>
      <div class="tx">🗣 {esc(short(w['transcript_en'] or w['transcript_original'],160))}</div>
      <div class="tx ocr">OCR: {esc(ocr)}</div>
      <div class="tx vis">👁 {esc(short(w['visual_description'],140))}</div></div>"""


def case_html(q, r):
    rb = r.get("retrieval", {})
    chunks = "".join(chunk_html(w) for w in rb.get("windows", []))
    n_cited = sum(1 for w in rb.get("windows", []) if w["cited_as_evidence"])
    mode_line = (f"mode=<b>{esc(rb.get('mode'))}</b> · retrieved={rb.get('n_retrieved')} "
                 f"chunk · đưa vào LLM={rb.get('n_in_context')} · trích dẫn={n_cited}")
    if rb.get("resolved_entity") or rb.get("matched_business_event"):
        mode_line += (f" · entity={esc(rb.get('resolved_entity'))}"
                      f" · event={esc(rb.get('matched_business_event'))}")
    fb = "found" if r["found"] else "KHÔNG TÌM THẤY"
    ans = f"""<div class="ans"><div class="abadge {'y' if r['found'] else 'n'}">{fb}</div>
      <div class="atext">{esc(r['answer'])}</div>
      <div class="rat">{esc(r.get('rationale',''))}</div></div>"""
    return f"""<div class="case">
      <div class="q">❓ {esc(q)}</div>
      <div class="meta">{mode_line}</div>
      <div class="cols"><div class="left"><div class="lbl">RETRIEVED (RAG lấy ra)</div>{chunks}</div>
        <div class="right"><div class="lbl">ANSWER (RAG trả lời)</div>{ans}</div></div></div>"""


CSS = """
body{font-family:system-ui,Segoe UI,Roboto,sans-serif;background:#0f1115;color:#e6e6e6;margin:0;padding:20px}
h1{font-size:20px}.sub{color:#9aa;margin-bottom:16px}
.case{background:#161922;border-radius:12px;padding:16px;margin:16px 0}
.q{font-size:17px;font-weight:700;color:#fff}.meta{color:#8ab;font-size:12px;margin:6px 0 12px}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.lbl{font-size:12px;letter-spacing:.5px;color:#7d8;text-transform:uppercase;margin-bottom:8px}
.chunk{background:#0e1117;border:1px solid #242a36;border-radius:8px;padding:8px;margin-bottom:8px}
.chunk.cited{border-color:#2ecc71;box-shadow:0 0 0 1px #2ecc71 inset}
.ch{display:flex;gap:8px;align-items:flex-start}.ch img{width:74px;border-radius:5px}
.bdg{color:#2ecc71;font-size:11px;font-weight:700}.ev{color:#789;font-size:11px;margin-top:2px}
.tx{font-size:12px;margin-top:5px;color:#cdd}.ocr{color:#7fd}.vis{color:#9b9}
.ans{background:#0e1117;border-radius:8px;padding:12px;position:sticky;top:10px}
.abadge{display:inline-block;padding:2px 10px;border-radius:6px;font-weight:700;font-size:12px;margin-bottom:8px}
.abadge.y{background:#16331f;color:#2ecc71}.abadge.n{background:#3a1a1a;color:#e74c3c}
.atext{line-height:1.55}.rat{color:#9bd;font-size:13px;margin-top:8px;border-top:1px solid #242a36;padding-top:8px}
"""


def main():
    gold = json.loads((Path(__file__).parent / "eval/gold.json").read_text("utf-8"))
    video_id = gold.get("video_id", "video_001")
    qs = [c for c in gold["cases"] if c["type"] == "qa"]

    cards = []
    for c in qs:
        r = qa.answer(video_id, c["question"], debug=True)
        cards.append(case_html(c["question"], r))
        print(f"  done: {c['id']}")

    doc = (f"<!doctype html><html><head><meta charset='utf-8'><title>RAG Inspect</title>"
           f"<style>{CSS}</style></head><body>"
           f"<h1>RAG Inspect — đối chiếu RETRIEVED ↔ ANSWER</h1>"
           f"<div class='sub'>video={video_id} · {len(qs)} câu · chunk viền xanh ★ = được trích dẫn làm bằng chứng</div>"
           f"{''.join(cards)}</body></html>")
    out = config.STORAGE / "rag_inspect.html"
    out.write_text(doc, "utf-8")
    print(f"\nMở file: {out}")


if __name__ == "__main__":
    main()
