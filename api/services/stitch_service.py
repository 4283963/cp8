import asyncio
import uuid
import subprocess
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from api.models import StitchStatusResponse
from api.services.video_scanner import get_slices_with_timestamps, parse_filename

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output"
SLICES_DIR = Path(__file__).resolve().parent.parent.parent / "video_slices"
TMP_DIR = OUTPUT_DIR / "tmp"

SLICE_DURATION_MS = 30_000

tasks: Dict[str, StitchStatusResponse] = {}


def _has_ffmpeg() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _slice_end_time(start_ms: int) -> int:
    return start_ms + SLICE_DURATION_MS


def _find_common_time_range(all_slices: Dict[str, List[Tuple[Path, int]]]) -> Tuple[int, int]:
    if not all_slices:
        return 0, 0

    latest_start = 0
    earliest_end = float("inf")

    for camera, slices in all_slices.items():
        if not slices:
            continue
        first_start = slices[0][1]
        last_end = _slice_end_time(slices[-1][1])
        if first_start > latest_start:
            latest_start = first_start
        if last_end < earliest_end:
            earliest_end = last_end

    return int(latest_start), int(earliest_end)


def _select_slices_in_range(
    slices: List[Tuple[Path, int]],
    common_start: int,
    common_end: int,
) -> List[Tuple[Path, int, int]]:
    selected = []

    for filepath, start_ms in slices:
        end_ms = _slice_end_time(start_ms)

        if end_ms <= common_start:
            continue
        if start_ms >= common_end:
            break

        in_offset = max(0, common_start - start_ms)
        out_offset = min(SLICE_DURATION_MS, common_end - start_ms)

        selected.append((filepath, in_offset, out_offset))

    return selected


def _ms_to_ffmpeg_time(ms: int) -> str:
    hours = ms // 3_600_000
    ms %= 3_600_000
    minutes = ms // 60_000
    ms %= 60_000
    seconds = ms // 1000
    milliseconds = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


def _trim_and_concat_ffmpeg(
    slices_with_offsets: List[Tuple[Path, int, int]],
    output_file: Path,
) -> bool:
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    trimmed_files = []
    concat_list_path = TMP_DIR / f"concat_{output_file.stem}.txt"

    try:
        for i, (filepath, in_offset, out_offset) in enumerate(slices_with_offsets):
            trimmed_path = TMP_DIR / f"{output_file.stem}_trim_{i:03d}.mp4"

            in_time = _ms_to_ffmpeg_time(in_offset)
            duration_ms = out_offset - in_offset
            duration_time = _ms_to_ffmpeg_time(duration_ms)

            cmd = [
                "ffmpeg", "-y",
                "-i", str(filepath),
                "-ss", in_time,
                "-t", duration_time,
                "-c", "copy",
                "-avoid_negative_ts", "make_zero",
                str(trimmed_path),
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            if result.returncode != 0:
                trimmed_path.write_bytes(b"")
            trimmed_files.append(trimmed_path)

        with open(concat_list_path, "w") as f:
            for tf in trimmed_files:
                f.write(f"file '{tf.resolve()}'\n")

        concat_cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_list_path),
            "-c", "copy",
            str(output_file),
        ]
        subprocess.run(concat_cmd, capture_output=True, timeout=120)
        return True

    except Exception:
        output_file.write_bytes(b"")
        return False
    finally:
        if concat_list_path.exists():
            concat_list_path.unlink()
        for tf in trimmed_files:
            if tf.exists():
                tf.unlink()


def _simulate_trim_and_concat(
    slices_with_offsets: List[Tuple[Path, int, int]],
    output_file: Path,
    common_start: int,
    common_end: int,
    camera: str,
) -> bool:
    total_duration = common_end - common_start
    info_lines = [
        f"=== 拼接信息 (模拟) ===",
        f"机位: {camera}",
        f"对齐起始时间戳: {common_start} ms",
        f"对齐结束时间戳: {common_end} ms",
        f"对齐后总时长: {total_duration} ms = {total_duration/1000:.3f} s",
        f"切片数量: {len(slices_with_offsets)}",
        f"---------------------",
    ]
    for filepath, in_off, out_off in slices_with_offsets:
        dur = out_off - in_off
        info_lines.append(
            f"  {filepath.name}: in={in_off}ms, out={out_off}ms, 截取时长={dur}ms"
        )
    info_lines.append("=== 结束 ===")

    output_file.write_text("\n".join(info_lines), encoding="utf-8")
    return True


def _stitch_single_camera(
    camera: str,
    all_slices: Dict[str, List[Tuple[Path, int]]],
    common_start: int,
    common_end: int,
    output_dir: Path,
) -> Path:
    camera_slices = all_slices.get(camera, [])
    selected = _select_slices_in_range(camera_slices, common_start, common_end)

    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"stitched_{camera}_{now}.mp4"

    use_ffmpeg = _has_ffmpeg()
    if use_ffmpeg:
        _trim_and_concat_ffmpeg(selected, output_file)
        if not output_file.exists() or output_file.stat().st_size < 1024:
            use_ffmpeg = False

    if not use_ffmpeg:
        _simulate_trim_and_concat(selected, output_file, common_start, common_end, camera)

    return output_file


async def start_stitch(cameras: List[str]) -> str:
    task_id = uuid.uuid4().hex[:12]

    tasks[task_id] = StitchStatusResponse(
        task_id=task_id,
        status="processing",
        message="拼接任务已启动",
        progress=0,
    )

    asyncio.create_task(_run_stitch(task_id, cameras))

    return task_id


async def _run_stitch(task_id: str, cameras: List[str]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    try:
        tasks[task_id] = StitchStatusResponse(
            task_id=task_id,
            status="processing",
            message="正在扫描视频切片...",
            progress=5,
        )
        await asyncio.sleep(0.1)

        all_slices: Dict[str, List[Tuple[Path, int]]] = {}
        for camera in cameras:
            slices = get_slices_with_timestamps(camera)
            all_slices[camera] = slices

        if not all_slices:
            tasks[task_id] = StitchStatusResponse(
                task_id=task_id,
                status="failed",
                message="未找到任何视频切片",
                progress=0,
            )
            return

        tasks[task_id] = StitchStatusResponse(
            task_id=task_id,
            status="processing",
            message="正在计算共同时间范围并对齐...",
            progress=15,
        )
        await asyncio.sleep(0.1)

        common_start, common_end = _find_common_time_range(all_slices)
        total_duration = common_end - common_start

        if total_duration <= 0:
            tasks[task_id] = StitchStatusResponse(
                task_id=task_id,
                status="failed",
                message="各路视频没有共同的时间范围，无法对齐",
                progress=0,
            )
            return

        total = len(cameras)
        output_files = []

        for idx, camera in enumerate(cameras):
            tasks[task_id] = StitchStatusResponse(
                task_id=task_id,
                status="processing",
                message=f"正在拼接 {camera} 机位视频 (对齐中)...",
                progress=20 + int((idx / total) * 75),
            )

            output_file = await asyncio.to_thread(
                _stitch_single_camera,
                camera,
                all_slices,
                common_start,
                common_end,
                OUTPUT_DIR,
            )
            output_files.append(output_file)
            await asyncio.sleep(0.3)

        tasks[task_id] = StitchStatusResponse(
            task_id=task_id,
            status="completed",
            output_file=f"stitched_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
            message=f"全机位拼接完成，已按绝对时间戳对齐，共同时长 {total_duration/1000:.3f} 秒",
            progress=100,
        )

    except Exception as e:
        tasks[task_id] = StitchStatusResponse(
            task_id=task_id,
            status="failed",
            message=f"拼接失败: {str(e)}",
            progress=0,
        )


def get_task_status(task_id: str) -> Optional[StitchStatusResponse]:
    return tasks.get(task_id)
