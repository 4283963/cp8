from fastapi import APIRouter
from api.models import VideosResponse
from api.services.video_scanner import scan_video_slices

router = APIRouter(prefix="/api", tags=["videos"])


@router.get("/videos", response_model=VideosResponse)
async def get_videos():
    return scan_video_slices()
