"""Streamlit demo — hỏi đáp RAG + đối chiếu RETRIEVED↔ANSWER, SKU timeline,
kiểm chứng/compliance, và chạy Gold eval. Gọn, tương tác.

Chạy (từ project root):
  backend/.venv/bin/streamlit run backend/streamlit_app.py
Mở: VSCode tự forward cổng 8501 -> bấm "Open in Browser".
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st  # noqa: E402

from app import config, db, qa, verification  # noqa: E402

st.set_page_config(page_title="SEA Video-RAG", layout="wide")
db.init_db()


def fs(path: str) -> str:
    """thumbnail URL ('/thumbs/..') -> đường dẫn file trên ổ đĩa cho st.image."""
    return str(config.STORAGE / (path or "").lstrip("/"))


def mmss(s):
    s = int(s or 0)
    return f"{s // 60:02d}:{s % 60:02d}"


@st.cache_data(show_spinner=False)
def chunk_plan(vid: str):
    """Tính lại kế hoạch chunk audio (VAD) để hiển thị mép block. Cache theo video."""
    from app import audio as A
    ap = config.AUDIO_DIR / f"{vid}.mp3"
    if not ap.exists():
        return None
    dur = A._duration(ap)
    sil = A._detect_silences(ap)
    return {"dur": dur, "n_sil": len(sil), "block_sec": A.BLOCK_SEC,
            "blocks": A.plan_blocks(dur, sil)}


# ── Sidebar: chọn video + metrics ────────────────────────────────────────────
videos = db.list_videos()
vids = [v["video_id"] for v in videos] or ["video_001"]
st.sidebar.title("🎥 SEA Video-RAG")
video_id = st.sidebar.selectbox("Video", vids)
vmeta = db.get_video(video_id) or {}
st.sidebar.caption(vmeta.get("filename", ""))

m = db.metrics(video_id)  # đọc lại mỗi lần rerun -> cập nhật sau từng câu hỏi
c1, c2 = st.sidebar.columns(2)
c1.metric("Chi phí", f"${m['cost_usd']:.4f}")
c2.metric("Số call", m["calls"])
c1.metric("Latency TB", f"{int(m['avg_latency_ms'])}ms")
c2.metric("Cache hit", f"{int(m['cache_hit_rate']*100)}%")
with st.sidebar.expander("Chi tiết theo stage", expanded=True):
    for s in m.get("by_stage", []):
        st.caption(f"**{s['stage']}**: {s['calls']} call · ${s['cost_usd']:.4f} · "
                   f"{int(s['avg_latency_ms'])}ms")
if st.sidebar.button("🔄 Làm mới metrics"):
    st.rerun()
st.sidebar.divider()
st.sidebar.subheader("Sản phẩm (SKU)")
ents = db.get_entities(video_id)
for e in ents:
    st.sidebar.write(f"**{e['entity_id']}** — {e['names'].get('en','')[:48]}")

tab_qa, tab_tx, tab_sku, tab_verify, tab_eval = st.tabs(
    ["💬 Hỏi đáp (RAG)", "📝 Transcript & Chunking", "📦 SKU timeline",
     "✅ Kiểm chứng & Compliance", "🧪 Gold eval"])


# ── Tab 1: Q&A + đối chiếu RETRIEVED↔ANSWER ──────────────────────────────────
SAMPLES = [
    "Người dẫn demo sản phẩm nào ở phút đầu?",
    "Khi nào người dẫn báo giá?",
    "Tìm các đoạn có nhắc giảm giá.",
    "Có lúc nào người dẫn nói chính hãng không?",
    "Sản phẩm nào được nhắc nhiều nhất?",
    "Tóm tắt timeline bán hàng của video.",
]
with tab_qa:
    st.caption("Hỏi tiếng Việt/Anh. Bên trái = câu trả lời; mở rộng để xem RAG đã lấy chunk nào (★ = dùng làm bằng chứng).")
    cols = st.columns(3)
    for i, s in enumerate(SAMPLES):
        if cols[i % 3].button(s, key=f"s{i}", use_container_width=True):
            st.session_state["q"] = s
    q = st.text_input("Câu hỏi", st.session_state.get("q", SAMPLES[0]))
    if st.button("🔎 Trả lời", type="primary"):
        with st.spinner("Đang truy hồi + tổng hợp..."):
            r = qa.answer(video_id, q, debug=True)
        st.session_state["last"] = r
        st.rerun()  # rerun -> sidebar đọc lại metrics (đã có call vừa rồi)

    r = st.session_state.get("last")
    if r:
        left, right = st.columns([3, 2])
        with left:
            if r["found"]:
                st.success("✅ FOUND — có bằng chứng")
            else:
                st.error("🚫 KHÔNG TÌM THẤY (từ chối trung thực)")
            st.markdown(f"**Trả lời:** {r['answer']}")
            if r.get("rationale"):
                st.markdown(f"*Lý do:* {r['rationale']}")
            if r.get("modalities"):
                st.write("Modalities:", " · ".join(r["modalities"]))
            st.caption(f"cost ${r['cost']:.4f} · {r['latency_ms']}ms")
            for ev in r.get("evidence", []):
                with st.container(border=True):
                    ec1, ec2 = st.columns([1, 3])
                    if ev.get("thumbnail_path"):
                        ec1.image(fs(ev["thumbnail_path"]), use_container_width=True)
                    ec2.markdown(f"**⏱ {mmss(ev['start_time'])}** · OCR: {', '.join(ev['ocr'][:5])}")
                    ec2.caption(f"🗣 {ev.get('transcript','')[:160]}")
                    ec2.caption(f"👁 {ev.get('visual_description','')[:140]}")
        with right:
            rb = r.get("retrieval", {})
            st.markdown(f"**RAG đã retrieve** · mode=`{rb.get('mode')}` · "
                        f"{rb.get('n_retrieved')} chunk · trích dẫn="
                        f"{sum(1 for w in rb.get('windows',[]) if w['cited_as_evidence'])}")
            for w in rb.get("windows", []):
                star = "★ " if w["cited_as_evidence"] else ""
                with st.expander(f"{star}{w['window_id']} · {mmss(w['start_time'])}-{mmss(w['end_time'])}"):
                    if w["thumbnail"]:
                        st.image(fs(w["thumbnail"]), width=160)
                    st.caption(f"events={w['business_events']} ent={w['entities']}")
                    st.write("🗣", (w["transcript_en"] or w["transcript_original"])[:200])
                    st.write("OCR:", ", ".join(w["ocr"][:8]))


# ── Tab: Transcript & Chunking (kiểm tra VAD + transcript) ───────────────────
with tab_tx:
    cp = chunk_plan(video_id)
    if cp:
        st.markdown(f"**Audio {cp['dur']:.0f}s · {cp['n_sil']} khoảng lặng · "
                    f"BLOCK_SEC={cp['block_sec']:.0f}s → {len(cp['blocks'])} block (cắt theo VAD)**")
        st.dataframe(
            [{"block": i + 1, "start": round(s, 1), "end": round(e, 1),
              "len (s)": round(e - s, 1)} for i, (s, e) in enumerate(cp["blocks"])],
            use_container_width=True, hide_index=True)
        st.caption("Mép block lệch khỏi mốc 30s đều = đã dịch vào chỗ im lặng → không cắt giữa câu.")
    wins = db.get_windows(video_id)
    st.subheader("Đường cong energy")
    st.line_chart({"energy": [w.energy for w in wins]})
    st.subheader("Transcript theo window (đa ngữ)")
    only_text = st.checkbox("Chỉ hiện window có thoại", True)
    for w in wins:
        if only_text and not (w.transcript_original or w.transcript_en):
            continue
        with st.container(border=True):
            st.markdown(f"**{w.window_id} · {mmss(w.start_time)}–{mmss(w.end_time)}** · "
                        f"🎙 {w.speaker or '—'} · ⚡ {w.energy} · 🔊 {', '.join(w.audio_events) or '—'}")
            if w.transcript_original:
                st.write("🗣", w.transcript_original)
            if w.transcript_en and w.transcript_en != w.transcript_original:
                st.caption("EN: " + w.transcript_en)


# ── Tab 2: SKU timeline ───────────────────────────────────────────────────────
with tab_sku:
    if ents:
        eid = st.selectbox("Chọn sản phẩm", [e["entity_id"] for e in ents],
                           format_func=lambda x: f"{x} — " +
                           next((e['names'].get('en','') for e in ents if e['entity_id']==x), ""))
        tl = db.get_timeline(video_id, eid)
        st.write(f"**{len(tl)} lần xuất hiện** (xếp theo độ rõ):")
        for o in tl:
            with st.container(border=True):
                cc1, cc2 = st.columns([1, 4])
                if o.get("thumbnail"):
                    cc1.image(fs(o["thumbnail"]), use_container_width=True)
                cc2.markdown(f"**⏱ {mmss(o['start_time'])}** · `{o['action']}` · "
                             f"visibility={o['visibility']}")
                cc2.caption(f"evidence: {o['evidence']}")
    else:
        st.info("Chưa có entity.")


# ── Tab 3: Verify + Compliance ────────────────────────────────────────────────
with tab_verify:
    st.subheader("Claim-vs-Visual")
    claim = st.text_input("Câu nói cần kiểm chứng", "sản phẩm này là hàng chính hãng")
    if st.button("Kiểm chứng"):
        with st.spinner("..."):
            rv = verification.verify_claim(video_id, claim)
        {"verified": st.success, "warning": st.warning}.get(rv["result"], st.error)(
            f"{rv['result']} · is_verified={rv['is_verified']}")
        st.write(rv["reason"])
        for ev in rv.get("evidence", []):
            if ev.get("thumbnail_path"):
                st.image(fs(ev["thumbnail_path"]), width=200)
            st.caption(f"⏱ {mmss(ev['start_time'])} · {ev.get('transcript','')[:160]}")

    st.divider()
    st.subheader("Compliance audit")
    if st.button("Quét compliance"):
        with st.spinner("Đang quét..."):
            rc = verification.compliance_scan(video_id)
        st.write(f"Đã kiểm {rc['checked']} mục · {len(rc['flags'])} cảnh báo · ${rc['cost']:.4f}")
        for f in rc["flags"]:
            with st.container(border=True):
                (st.error if f["severity"] == "high" else st.warning)(
                    f"[{f['severity']}] {f['rule']} → {f['result']}")
                st.write(f["reason"])
                ev = f["evidence"][0]
                if ev.get("thumbnail_path"):
                    st.image(fs(ev["thumbnail_path"]), width=200)
                st.caption(f"⏱ {mmss(ev['start_time'])} · {ev.get('transcript','')[:160]}")


# ── Tab 4: Gold eval ──────────────────────────────────────────────────────────
with tab_eval:
    st.caption("Chạy bộ câu hỏi mẫu (backend/eval/gold.json) và tự chấm PASS/FAIL.")
    if st.button("▶️ Chạy Gold eval"):
        import json
        from eval_rag import DISPATCH, OK
        gold = json.loads((Path(__file__).parent / "eval/gold.json").read_text("utf-8"))
        tol = gold.get("tolerance_sec", 8)
        rows, npass = [], 0
        prog = st.progress(0.0)
        for i, c in enumerate(gold["cases"]):
            verdict, checks, reasons, snippet, cost, _ = DISPATCH[c["type"]](c, video_id, tol)
            npass += verdict == OK
            rows.append({"id": c["id"], "type": c["type"],
                         "verdict": "✅" if verdict == OK else "❌",
                         "q": c.get("question") or c.get("claim") or c.get("entity_id"),
                         "answer": snippet, "lý do fail": "; ".join(reasons)})
            prog.progress((i + 1) / len(gold["cases"]))
        st.metric("Kết quả", f"{npass}/{len(gold['cases'])} PASS")
        st.dataframe(rows, use_container_width=True)
