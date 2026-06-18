from fastapi import APIRouter, HTTPException
from api.models import StitchRequest, StitchResponse, StitchStatusResponse
from api.services.stitch_service import start_stitch, get_task_status

router = APIRouter(prefix="/api", tags=["stitch"])


@router.post("/stitch", response_model=StitchResponse)
async def stitch_videos(request: StitchRequest):
    task_id = await start_stitch(request.cameras)
    return StitchResponse(
        task_id=task_id,
        status="processing",
        message="拼接任务已启动",
    )


@router.get("/stitch/{task_id}", response_model=StitchStatusResponse)
async def get_stitch_status(task_id: str):
    status = get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="任务不存在")
    return status
