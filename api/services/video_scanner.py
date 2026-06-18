import os
import re
from pathlib import Path
from typing import List, Dict
from api.models import VideoSlice, VideoSummary, VideosResponse

SLICES_DIR = Path(__file__).resolve().parent.parent.parent / "video_slices"

CAMERAS = ["front", "rear", "left", "right"]

TIMESTAMP_PATTERN = re.compile(r"(\w+)_(\d{8}_\d{6})\.mp4")


def scan_video_slices() -> VideosResponse:
    slices: List[VideoSlice] = []
    summary_dict: Dict[str, int] = {cam: 0 for cam in CAMERAS}

    for camera in CAMERAS:
        camera_dir = SLICES_DIR / camera
        if not camera_dir.exists():
            continue

        for f in sorted(camera_dir.iterdir()):
            if not f.is_file() or not f.name.endswith(".mp4"):
                continue

            match = TIMESTAMP_PATTERN.match(f.name)
            if not match:
                continue

            cam_label = match.group(1)
            ts_raw = match.group(2)
            ts_formatted = f"{ts_raw[:4]}-{ts_raw[4:6]}-{ts_raw[6:8]} {ts_raw[9:11]}:{ts_raw[11:13]}:{ts_raw[13:15]}"

            size_kb = f.stat().st_size // 1024

            slices.append(VideoSlice(
                filename=f.name,
                camera=cam_label,
                timestamp=ts_formatted,
                size_kb=size_kb,
            ))
            summary_dict[camera] += 1

    slices.sort(key=lambda s: s.timestamp, reverse=True)

    return VideosResponse(
        slices=slices,
        summary=VideoSummary(**summary_dict),
    )


def get_slices_for_camera(camera: str) -> List[Path]:
    camera_dir = SLICES_DIR / camera
    if not camera_dir.exists():
        return []

    files = sorted(
        [f for f in camera_dir.iterdir() if f.is_file() and f.name.endswith(".mp4")],
        key=lambda f: f.name,
    )
    return files
