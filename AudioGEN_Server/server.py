import logging
import traceback
from pathlib import Path
from typing import List
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel as PydanticBaseModel
from generate_audios import AudioGenerator, build_full_narration


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Audio Generator API",
    description="Generate Audio from storyboard using provided task_id",
    version="1.0"
)

TASKS_DIR = Path("./server_tasks")
TASKS_DIR.mkdir(exist_ok=True)
try:
    generator = AudioGenerator(voice="zh-CN-YunxiNeural")
except Exception as e:
    logger.critical(f"Failed to initialize AudioGenerator: {e}")
    generator = None


class Scene(PydanticBaseModel):
    scene_title: str
    narration: str
    bgm_suggestion: str
    prompt: dict


class GenerateRequest(PydanticBaseModel):
    task_id: str
    storyboard: List[Scene]  # scenes 列表


class GenerateResponse(PydanticBaseModel):
    task_id: str
    audio_paths: List[str]


@app.post("/generate/audios", response_model=GenerateResponse)
async def generate_audios(request: Request, req: GenerateRequest):
    if generator is None:
        raise HTTPException(status_code=500, detail="Image generator init error")

    client_ip = request.client.host or "unknown"
    logger.info(f"[{req.task_id}] Received request from {client_ip} for {len(req.storyboard)} scenes")

    task_dir = TASKS_DIR / req.task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    try:
        audio_paths = []
        for i, scene in enumerate(req.storyboard, 1):
            logger.info(f"\n--- Scene {i} ---")
            full_narration = build_full_narration(scene.model_dump())
            print(f"Text: {full_narration}")
            audio_path = await generator.generate(
                text=full_narration,
                output_dir=str(task_dir),
                counter=i
            )
            audio_paths.append(Path(audio_path).name)
        logger.info("All audios generated!")
        return GenerateResponse(task_id=req.task_id, audio_paths=audio_paths)

    except Exception as e:
        error_msg = f"[{req.task_id}] Audio generation error: {str(e)}"
        logger.error(error_msg)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/health")
async def health_check():
    return {
        "status": "ok" if generator is not None else "failed",
        "model": "edge_tts"
    }


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
    uvicorn.run(app="server:app", host="0.0.0.0", port=8004, log_level="info")
