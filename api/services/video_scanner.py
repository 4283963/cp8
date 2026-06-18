import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from api.models import VideoSlice, VideoSummary, VideosResponse

SLICES_DIR = Path(__file__).resolve().parent.parent.parent / "video_slices"

CAMERAS = ["front", "rear", "left", "right"]

TIMESTAMP_PATTERN = re.compile(
    r"(\w+)_(\d{8})_(\d{6})(?:_(\d{3}))?\.mp4"
)

SLICE_DURATION_MS = 30_000


def parse_filename(filename: str) -> Optional[Tuple[str, int]]:
    match = TIMESTAMP_PATTERN.match(filename)
    if not match:
        return None

    camera = match.group(1)
    date_str = match.group(2)
    time_str = match.group(3)
    ms_str = match.group(4) or "000"

    dt_str = f"{date_str}_{time_str}.{ms_str}000"
    dt = datetime.strptime(dt_str, "%Y%m%d_%H%M%S.%f")
    ts_ms = int(dt.timestamp() * 1000)

    return camera, ts_ms


def format_timestamp(ts_ms: int) -> str:
    dt = datetime.fromtimestamp(ts_ms / 1000.0)
    return dt.strftime("%Y-%m-%d %H:%M:%S") + f".{ts_ms % 1000:03d}"


def scan_video_slices() -> VideosResponse:
    slices: List[VideoSlice] = []
    count_dict: Dict[str, int] = {cam: 0 for cam in CAMERAS}
    status_dict: Dict[str, str] = {}

    for camera in CAMERAS:
        camera_dir = SLICES_DIR / camera
        if not camera_dir.exists():
            status_dict[f"{camera}_status"] = "lost"
            continue

        cam_slices = []
        for f in sorted(camera_dir.iterdir()):
            if not f.is_file() or not f.name.endswith(".mp4"):
                continue

            parsed = parse_filename(f.name)
            if not parsed:
                continue

            cam_label, ts_ms = parsed
            size_kb = f.stat().st_size // 1024

            cam_slices.append(VideoSlice(
                filename=f.name,
                camera=cam_label,
                timestamp=format_timestamp(ts_ms),
                size_kb=size_kb,
            ))

        count_dict[camera] = len(cam_slices)
        status_dict[f"{camera}_status"] = "ok" if cam_slices else "lost"
        slices.extend(cam_slices)

    slices.sort(key=lambda s: s.timestamp, reverse=True)

    summary_data = {**count_dict, **status_dict}
    return VideosResponse(
        slices=slices,
        summary=VideoSummary(**summary_data),
    )


def get_slices_with_timestamps(camera: str) -> List[Tuple[Path, int]]:
    camera_dir = SLICES_DIR / camera
    if not camera_dir.exists():
        return []

    result = []
    for f in camera_dir.iterdir():
        if not f.is_file() or not f.name.endswith(".mp4"):
            continue
        parsed = parse_filename(f.name)
        if not parsed:
            continue
        result.append((f, parsed[1]))

    result.sort(key=lambda x: x[1])
    return result
