from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.videos import router as videos_router
from api.routes.stitch import router as stitch_router

app = FastAPI(title="行车记录仪视频管理与拼接系统", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(videos_router)
app.include_router(stitch_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
