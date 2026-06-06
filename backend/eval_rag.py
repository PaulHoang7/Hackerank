"""RAG evaluation harness — đặt câu hỏi + đối chiếu đáp án kỳ vọng -> PASS/FAIL.

Gold set (chỗ bạn sửa kỳ vọng): backend/eval/gold.json
Chạy:
  backend/.venv/bin/python backend/eval_rag.py
  backend/.venv/bin/python backend/eval_rag.py --gold backend/eval/gold.json --video_id video_001
Báo cáo ghi ra: backend/eval/last_report.json
"""
import argparse
import json
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import qa, verification  # noqa: E402

OK, NO = "PASS", "FAIL"


def _short(s, n=160):
    return textwrap.shorten((s or "").replace("\n", " "), n)


def _kw_check(answer, anys, alls):
    a = (answer or "").lower()
    if anys and not any(k.lower() in a for k in anys):
        return False, f"thiếu mọi từ-khóa-any {anys}"
    if alls and not all(k.lower() in a for k in alls):
        return False, f"thiếu vài từ-khóa-all {alls}"
    return True, ""


def _time_check(evidence, expected, tol):
    if not expected:
        return True, ""
    missing = []
    for t in expected:
        hit = any(e["start_time"] - tol <= t <= e["end_time"] + tol for e in evidence)
        if not hit:
            missing.append(t)
    if missing:
        return False, f"evidence không phủ giây {missing} (±{tol}s)"
    return True, ""


def eval_qa(case, video_id, tol):
    r = qa.answer(video_id, case["question"])
    checks, reasons = [], []

    if "expect_found" in case:
        ok = r["found"] == case["expect_found"]
        checks.append(("found", ok))
        if not ok:
            reasons.append(f"found exp={case['expect_found']} act={r['found']}")

    # nội dung/evidence chỉ kiểm khi kỳ vọng tìm thấy
    if case.get("expect_found", True):
        ok, why = _kw_check(r["answer"], case.get("expect_keywords_any"),
                            case.get("expect_keywords_all"))
        checks.append(("keywords", ok))
        if not ok:
            reasons.append(why)
        ok, why = _time_check(r["evidence"], case.get("expect_time_contains"), tol)
        checks.append(("time", ok))
        if not ok:
            reasons.append(why)

    verdict = OK if all(ok for _, ok in checks) else NO
    return verdict, checks, reasons, _short(r["answer"]), r.get("cost", 0), r


def eval_verify(case, video_id, tol):
    r = verification.verify_claim(video_id, case["claim"])
    checks, reasons = [], []
    if "expect_result" in case:
        ok = r["result"] == case["expect_result"]
        checks.append(("result", ok))
        if not ok:
            reasons.append(f"result exp={case['expect_result']} act={r['result']}")
    if "expect_is_verified" in case:
        ok = r["is_verified"] == case["expect_is_verified"]
        checks.append(("is_verified", ok))
        if not ok:
            reasons.append(f"is_verified exp={case['expect_is_verified']} act={r['is_verified']}")
    verdict = OK if all(ok for _, ok in checks) else NO
    return verdict, checks, reasons, _short(r["reason"]), r.get("cost", 0), r


def eval_temporal(case, video_id, tol):
    r = verification.temporal(video_id, entity_id=case.get("entity_id"),
                              business_event=case.get("business_event"))
    checks, reasons = [], []
    cmin = case.get("expect_count_min", 1)
    ok = r["count"] >= cmin
    checks.append(("count", ok))
    if not ok:
        reasons.append(f"count={r['count']} < expect_min={cmin}")
    verdict = OK if ok else NO
    return verdict, checks, reasons, f"count={r['count']}", 0.0, r


DISPATCH = {"qa": eval_qa, "verify": eval_verify, "temporal": eval_temporal}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", default=str(Path(__file__).parent / "eval/gold.json"))
    ap.add_argument("--video_id", default=None)
    args = ap.parse_args()

    gold = json.loads(Path(args.gold).read_text("utf-8"))
    video_id = args.video_id or gold.get("video_id", "video_001")
    tol = gold.get("tolerance_sec", 8)

    print(f"\n=== RAG EVAL · video={video_id} · {len(gold['cases'])} cases ===\n")
    rows, n_pass, total_cost = [], 0, 0.0
    for c in gold["cases"]:
        verdict, checks, reasons, snippet, cost, raw = DISPATCH[c["type"]](c, video_id, tol)
        total_cost += cost
        n_pass += verdict == OK
        chk = " ".join(f"{name}{'✓' if ok else '✗'}" for name, ok in checks)
        mark = "✅" if verdict == OK else "❌"
        print(f"{mark} [{c['id']:11}] {verdict}  ({c['type']})  {chk}")
        print(f"     Q: {c.get('question') or c.get('claim') or c.get('entity_id')}")
        print(f"     A: {snippet}")
        if reasons:
            print(f"     ✗ vì: {'; '.join(reasons)}")
        print(f"     ghi chú: {c.get('note','')}")
        print()
        rows.append({"id": c["id"], "verdict": verdict, "checks": dict(checks),
                     "reasons": reasons, "answer": snippet, "cost": cost})

    rate = round(100 * n_pass / len(gold["cases"]), 1)
    print(f"=== TỔNG: {n_pass}/{len(gold['cases'])} PASS ({rate}%) · chi phí ${total_cost:.4f} ===")
    report = {"video_id": video_id, "passed": n_pass, "total": len(gold["cases"]),
              "pass_rate": rate, "cost_usd": round(total_cost, 4), "cases": rows}
    out = Path(__file__).parent / "eval/last_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), "utf-8")
    print(f"Báo cáo: {out}")
    sys.exit(0 if n_pass == len(gold["cases"]) else 1)


if __name__ == "__main__":
    main()
