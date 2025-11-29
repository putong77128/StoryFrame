import logging
import traceback
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel as PydanticBaseModel

from generator_tts import TTSGenerator, build_full_narration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Audio(TTS) Generator API",
    description="Generate audios from storyboard using provided task_id",
    version="1.0",
)

# 任务目录：与其它服务保持同一风格
TASKS_DIR = Path("./server_tasks")
TASKS_DIR.mkdir(exist_ok=True)

try:
    # 默认语音；真正使用时，可以在请求中传入 voice 覆盖
    tts_generator = TTSGenerator(default_voice="zh-CN-XiaoxiaoNeural")
except Exception as e:
    logger.critical(f"Failed to initialize TTSGenerator: {e}")
    tts_generator = None


# ======== Pydantic 数据模型 ========

class Scene(PydanticBaseModel):
    scene_title: str
    narration: str
    bgm_suggestion: Optional[str] = ""
    prompt: dict


class GenerateRequest(PydanticBaseModel):
    task_id: str
    storyboard: List[Scene]  # scenes 列表
    # voice 是可选字段，Main_Server 不传也没问题
    voice: Optional[str] = None


class GenerateResponse(PydanticBaseModel):
    task_id: str
    audio_paths: List[str]


# ======== 路由：生成音频 ========

# 同时兼容 /generate/audio 和 /generate/audios
@app.post("/generate/audio", response_model=GenerateResponse)
@app.post("/generate/audios", response_model=GenerateResponse)
async def generate_audios(request: Request, req: GenerateRequest):

    if tts_generator is None:
        raise HTTPException(status_code=500, detail="TTS generator init error")

    client_ip = request.client.host or "unknown"
    logger.info(
        f"[{req.task_id}] Received request from {client_ip} "
        f"for {len(req.storyboard)} scenes, voice={req.voice or 'default'}"
    )

    task_dir = TASKS_DIR / req.task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    try:
        audio_paths: List[str] = []
        for i, scene in enumerate(req.storyboard, 1):
            logger.info(f"\n--- Scene {i} ---")
            full_text = build_full_narration(scene.model_dump())
            logger.info(f"Text: {full_text!r}")

            audio_path = await tts_generator.generate(
                text=full_text,
                output_dir=str(task_dir),
                counter=i,
                voice=req.voice,   # 若为 None，则在 generator 内用默认值
            )
            audio_paths.append(Path(audio_path).name)

        logger.info(f"[{req.task_id}] All audios generated!")
        return GenerateResponse(task_id=req.task_id, audio_paths=audio_paths)

    except Exception as e:
        error_msg = f"[{req.task_id}] Audio generation error: {str(e)}"
        logger.error(error_msg)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)


# ======== 健康检查 ========

@app.get("/health")
async def health_check():
    return {
        "status": "ok" if tts_generator is not None else "failed",
        "model": "edge-tts",
    }

# ======== 下载接口：与 Main_Server 对齐 ========

@app.get("/download/{task_id}/{filename}")
def download_file(task_id: str, filename: str):

    file_path = TASKS_DIR.resolve() / task_id / filename
    try:
        file_path.relative_to(TASKS_DIR.resolve())
    except ValueError:
        raise HTTPException(403, "Access denied")

    if not file_path.is_file():
        raise HTTPException(404, "File not found")

    return FileResponse(file_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app="server:app", host="0.0.0.0", port=9000, log_level="info")
