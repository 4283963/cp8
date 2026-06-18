from pydantic import BaseModel
from typing import Literal, Optional, List


class VideoSlice(BaseModel):
    filename: str
    camera: Literal["front", "rear", "left", "right"]
    timestamp: str
    size_kb: int


class VideoSummary(BaseModel):
    front: int
    rear: int
    left: int
    right: int
    front_status: Literal["ok", "lost"]
    rear_status: Literal["ok", "lost"]
    left_status: Literal["ok", "lost"]
    right_status: Literal["ok", "lost"]


class VideosResponse(BaseModel):
    slices: List[VideoSlice]
    summary: VideoSummary


class StitchRequest(BaseModel):
    cameras: List[Literal["front", "rear", "left", "right"]] = [
        "front", "rear", "left", "right"
    ]


class StitchResponse(BaseModel):
    task_id: str
    status: Literal["processing", "completed", "failed"]
    output_file: Optional[str] = None
    message: str


class StitchStatusResponse(BaseModel):
    task_id: str
    status: Literal["processing", "completed", "failed"]
    output_file: Optional[str] = None
    message: str
    progress: int
