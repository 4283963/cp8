import os
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent / "video_slices"
CAMERAS = ["front", "rear", "left", "right"]

now = datetime.now()
start = now - timedelta(minutes=5)

for camera in CAMERAS:
    camera_dir = BASE_DIR / camera
    camera_dir.mkdir(parents=True, exist_ok=True)

    for existing in camera_dir.glob("*.mp4"):
        existing.unlink()

    ts = start
    while ts <= now:
        filename = f"{camera}_{ts.strftime('%Y%m%d_%H%M%S')}.mp4"
        filepath = camera_dir / filename
        size_kb = 800 + (hash(filename) % 400)
        filepath.write_bytes(os.urandom(size_kb * 1024))
        ts += timedelta(seconds=30)

print("模拟视频切片已生成完毕")
