"""CLI: index a video through the full pipeline and print a summary.

Usage (from project root):
  backend/.venv/bin/python backend/index_video.py "ScreenRecording_....mp4"
  backend/.venv/bin/python backend/index_video.py /abs/path/video.mp4 --id video_002
  backend/.venv/bin/python backend/index_video.py data/clip.mp4 --no-cache
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import config, pipeline  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Index a video (Seed 2.0 Lite pipeline).")
    ap.add_argument("source", help="video filename under data/ or an absolute path")
    ap.add_argument("--id", dest="video_id", default=None, help="video_id (default: stem)")
    ap.add_argument("--no-cache", action="store_true", help="ignore cached stage outputs")
    args = ap.parse_args()

    p = Path(args.source)
    src = p if p.is_absolute() else (config.DATA_DIR / args.source
                                     if not p.exists() else p)
    if not src.exists():
        sys.exit(f"not found: {src}")
    vid = args.video_id or "".join(c if c.isalnum() else "_" for c in src.stem)[:48]

    print(f"Indexing {src.name} as '{vid}' ...")
    t = time.time()
    summary = pipeline.run(str(src), vid, use_cache=not args.no_cache)
    summary["wall_seconds"] = round(time.time() - t, 1)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
