import sys, textwrap; sys.path.insert(0,"backend")
from app import qa, db, verification as v

def mode(q): return "EXHAUSTIVE" if any(h in q.lower() for h in qa.EXHAUSTIVE_HINTS) else "point"
def short(s,n=240): return textwrap.shorten(s.replace("\n"," "), n)

questions = [
 "Người dẫn demo sản phẩm nào ở phút đầu?",
 "Tìm mọi lần xuất hiện chữ FREE SHIP.",
 "Khi nào người dẫn báo giá?",
 "Sản phẩm nào được cầm lên trước camera?",
 "Tìm các đoạn có nhắc giảm giá.",
 "Có lúc nào người dẫn nói miễn phí vận chuyển không?",
 "Có lúc nào người dẫn nói chính hãng không?",
 "Sản phẩm nào được nhắc nhiều nhất?",
 "Tóm tắt timeline bán hàng của video.",
]
for i,q in enumerate(questions,1):
    r = qa.answer("video_001", q)
    print(f"\n[{i}] ({mode(q)}) {q}")
    print(f"    found={r['found']} mods={r['modalities']} ${r['cost']} {r['latency_ms']}ms")
    print("    A:", short(r['answer']))
    for ev in r['evidence'][:3]:
        print(f"     • {ev['start_time']}s ocr={ev['ocr'][:4]} thumb={ev['thumbnail_path']}")

print("\n[10] verify(claim='chính hãng') — hình ảnh có chứng minh không?")
rv = v.verify_claim("video_001", "sản phẩm này là hàng chính hãng")
print(f"    result={rv['result']} is_verified={rv['is_verified']} ${rv['cost']}")
print("    reason:", short(rv['reason']))

print("\n[ground-truth #9] số occurrence mỗi SKU:")
for e in db.get_entities("video_001"):
    tl = db.get_timeline("video_001", e["entity_id"])
    print(f"    {e['entity_id']} ({e['names']['en'][:38]}): {len(tl)} lần")
