import sys, time; sys.path.insert(0, "backend")
from pathlib import Path
from app import ingestion as ing
src = sorted(Path("data").glob("*.mp4"))[0]
print("SRC:", src.name)
t0=time.time()
meta, windows, proxy, audio = ing.ingest(src, "video_001")
dt=time.time()-t0
print(f"ingest took {dt:.1f}s")
print("meta:", meta.model_dump())
print("proxy:", proxy, proxy.stat().st_size//1024, "KB")
print("audio:", audio, (audio.stat().st_size//1024 if audio else None), "KB")
print("num_windows:", len(windows))
for w in windows[:5]:
    print(f"  {w.window_id} {w.start_time:.1f}-{w.end_time:.1f}s sub={w.sub_split} thumbs={len(w.thumbnails)} {w.thumbnails[:1]}")
print("  ...")
print("last:", windows[-1].window_id, f"{windows[-1].start_time:.1f}-{windows[-1].end_time:.1f}")
# gap check
gaps=sum(1 for a,b in zip(windows,windows[1:]) if abs(b.start_time-a.end_time)>0.05)
print("contiguity gaps:", gaps, "| coverage end:", windows[-1].end_time, "/", meta.duration)
