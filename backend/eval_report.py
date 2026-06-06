"""Tạo báo cáo HTML để CHECK ĐÚNG/SAI bằng mắt: mỗi câu hỏi hiển thị câu trả lời
của RAG + ảnh frame thật (thumbnail) + timestamp + OCR + transcript, kèm đáp án
kỳ vọng và auto PASS/FAIL.

Chạy:  backend/.venv/bin/python backend/eval_report.py
Mở:    storage/eval_report.html  (mở bằng trình duyệt)
"""
import base64
import html
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import config  # noqa: E402
from eval_rag import DISPATCH, OK, _short  # noqa: E402

_b64_cache: dict[str, str] = {}


def thumb_uri(path: str) -> str:
    """Đọc thumbnail từ ổ đĩa -> data URI để nhúng thẳng vào HTML (tự chứa)."""
    if not path:
        return ""
    if path in _b64_cache:
        return _b64_cache[path]
    fp = config.STORAGE / path.lstrip("/")
    if not fp.exists():
        return ""
    uri = "data:image/jpeg;base64," + base64.b64encode(fp.read_bytes()).decode()
    _b64_cache[path] = uri
    return uri


def fmt_t(s):
    s = int(s or 0)
    return f"{s // 60:02d}:{s % 60:02d}"


def esc(s):
    return html.escape(str(s or ""))


def ev_card(ev):
    uri = thumb_uri(ev.get("thumbnail_path") or ev.get("thumbnail"))
    img = f'<img src="{uri}">' if uri else '<div class="noimg">no frame</div>'
    ocr = ", ".join(ev.get("ocr", [])[:6])
    tr = ev.get("transcript", "") or ev.get("transcript_en", "")
    vis = ev.get("visual_description", "")
    return f"""<div class="ev">{img}
      <div class="evb"><b>⏱ {fmt_t(ev.get('start_time'))}</b>
      <div class="ocr">OCR: {esc(ocr)}</div>
      <div class="tr">🗣 {esc(_short(tr,140))}</div>
      <div class="vis">👁 {esc(_short(vis,140))}</div></div></div>"""


def render_case(c, verdict, checks, reasons, raw):
    badge = "pass" if verdict == OK else "fail"
    q = c.get("question") or c.get("claim") or f"{c.get('entity_id')} ∩ {c.get('business_event')}"
    chk = " ".join(f"<span class='c {'y' if ok else 'n'}'>{n}{'✓' if ok else '✗'}</span>"
                   for n, ok in checks)
    head = f"""<div class="card {badge}">
      <div class="top"><span class="vb {badge}">{verdict}</span>
        <span class="id">{esc(c['id'])} · {esc(c['type'])}</span> {chk}</div>
      <div class="q">❓ {esc(q)}</div>
      <div class="exp">🎯 Kỳ vọng: {esc(c.get('note',''))}</div>"""

    body = ""
    if c["type"] == "qa":
        mods = " ".join(f"<span class='mod'>{esc(m)}</span>" for m in raw.get("modalities", []))
        body += f"""<div class="ans"><b>Trả lời ({'FOUND' if raw['found'] else 'KHÔNG TÌM THẤY'}):</b>
          {esc(raw['answer'])}</div>
          <div class="rat">{esc(raw.get('rationale',''))} {mods}</div>"""
        evs = raw.get("evidence", [])
        if evs:
            body += '<div class="evs">' + "".join(ev_card(e) for e in evs[:4]) + "</div>"
    elif c["type"] == "verify":
        body += f"""<div class="ans"><b>Kết quả: {esc(raw['result'])}</b> (is_verified={raw['is_verified']})
          <br>{esc(raw['reason'])}</div>"""
        body += '<div class="evs">' + "".join(ev_card(e) for e in raw.get("evidence", [])) + "</div>"
    elif c["type"] == "temporal":
        body += f"<div class='ans'><b>{raw['count']} đoạn khớp</b></div>"
        body += '<div class="evs">' + "".join(ev_card(e) for e in raw.get("matches", [])[:6]) + "</div>"

    if reasons:
        body += f"<div class='why'>✗ {esc('; '.join(reasons))}</div>"
    return head + body + "</div>"


CSS = """
body{font-family:system-ui,Segoe UI,Roboto,sans-serif;background:#0f1115;color:#e6e6e6;margin:0;padding:24px}
h1{font-size:20px} .sum{color:#aaa;margin-bottom:18px}
.card{background:#1a1d24;border-radius:12px;padding:16px;margin:14px 0;border-left:6px solid #444}
.card.pass{border-left-color:#2ecc71} .card.fail{border-left-color:#e74c3c}
.top{display:flex;gap:10px;align-items:center;margin-bottom:8px}
.vb{font-weight:700;padding:2px 10px;border-radius:6px} .vb.pass{background:#16331f;color:#2ecc71} .vb.fail{background:#3a1a1a;color:#e74c3c}
.id{color:#8aa;font-size:13px} .c{font-size:12px;padding:1px 6px;border-radius:4px} .c.y{color:#2ecc71} .c.n{color:#e74c3c}
.q{font-size:16px;font-weight:600;margin:6px 0} .exp{color:#e0b050;font-size:13px;margin-bottom:8px}
.ans{background:#11141a;padding:10px;border-radius:8px;line-height:1.5} .rat{color:#9bd;font-size:13px;margin:6px 0}
.mod{background:#223;padding:1px 7px;border-radius:10px;font-size:11px;margin-left:4px}
.evs{display:flex;flex-wrap:wrap;gap:10px;margin-top:10px}
.ev{width:200px;background:#11141a;border-radius:8px;overflow:hidden} .ev img{width:200px;display:block}
.noimg{height:120px;display:flex;align-items:center;justify-content:center;color:#666}
.evb{padding:8px;font-size:12px} .ocr{color:#7fd}.tr{color:#ddd;margin:3px 0}.vis{color:#9b9}
.why{color:#e74c3c;margin-top:8px;font-size:13px}
"""


def main():
    gold = json.loads((Path(__file__).parent / "eval/gold.json").read_text("utf-8"))
    video_id = gold.get("video_id", "video_001")
    tol = gold.get("tolerance_sec", 8)

    cards, n_pass, cost = [], 0, 0.0
    for c in gold["cases"]:
        verdict, checks, reasons, snippet, cc, raw = DISPATCH[c["type"]](c, video_id, tol)
        n_pass += verdict == OK
        cost += cc
        cards.append(render_case(c, verdict, checks, reasons, raw))
        print(f"  {'OK ' if verdict==OK else 'XX '} {c['id']}")

    n = len(gold["cases"])
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    summary = (f"video={video_id} · {n_pass}/{n} PASS ({round(100*n_pass/n,1)}%) · "
               f"chi phí ${cost:.4f} · {ts}")
    doc = (f"<!doctype html><html><head><meta charset='utf-8'><title>RAG Eval</title>"
           f"<style>{CSS}</style></head><body><h1>RAG Eval — check đúng/sai bằng mắt</h1>"
           f"<div class='sum'>{summary}</div>{''.join(cards)}</body></html>")
    out = config.STORAGE / "eval_report.html"
    out.write_text(doc, "utf-8")
    print(f"\n{summary}\nMở file: {out}")


if __name__ == "__main__":
    main()
