import os
import random
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent / "video_slices"
CAMERAS = ["front", "rear", "left", "right"]

SLICE_DURATION_MS = 30_000
TOTAL_DURATION_MS = 5 * 60 * 1000

CAMERA_OFFSETS_MS = {
    "front": 0,
    "rear": 1200,
    "left": 3800,
    "right": 700,
}

now = datetime.now()
now_ts_ms = int(now.timestamp() * 1000)
start_ts_ms = now_ts_ms - TOTAL_DURATION_MS


def ts_to_filename(ts_ms: int, camera: str) -> str:
    dt = datetime.fromtimestamp(ts_ms / 1000.0)
    date_str = dt.strftime("%Y%m%d")
    time_str = dt.strftime("%H%M%S")
    ms = ts_ms % 1000
    return f"{camera}_{date_str}_{time_str}_{ms:03d}.mp4"


for camera in CAMERAS:
    camera_dir = BASE_DIR / camera
    camera_dir.mkdir(parents=True, exist_ok=True)

    for existing in camera_dir.glob("*.mp4"):
        existing.unlink()

    offset_ms = CAMERA_OFFSETS_MS[camera]
    cam_start_ms = start_ts_ms + offset_ms

    ts_ms = cam_start_ms
    slice_idx = 0
    while ts_ms + SLICE_DURATION_MS <= now_ts_ms:
        filename = ts_to_filename(ts_ms, camera)
        filepath = camera_dir / filename

        base_size = 800
        variance = hash(filename) % 400
        size_kb = base_size + variance
        filepath.write_bytes(os.urandom(size_kb * 1024))

        ts_ms += SLICE_DURATION_MS
        slice_idx += 1

    print(f"{camera}: 生成了 {slice_idx} 个切片，起始偏移 {offset_ms}ms")

print("模拟视频切片已生成完毕（含毫秒级时间戳和机位偏移）")
