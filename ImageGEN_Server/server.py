import logging
import traceback
from pathlib import Path
from typing import List
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel as PydanticBaseModel
from generate_images import ImageGenerator, build_full_prompt


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger("diffusers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)


app = FastAPI(
    title="Image Generator API",
    description="Generate images from storyboard using provided task_id",
    version="1.0"
)

TASKS_DIR = Path("./server_tasks")
TASKS_DIR.mkdir(exist_ok=True)
try:
    generator = ImageGenerator()
except Exception as e:
    logger.critical(f"Failed to initialize ImageGenerator: {e}")
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
    image_paths: List[str]


@app.post("/generate/images", response_model=GenerateResponse)
async def generate_images(request: Request, req: GenerateRequest):
    if generator is None:
        raise HTTPException(status_code=500, detail="Image generator init error")

    client_ip = request.client.host or "unknown"
    logger.info(f"[{req.task_id}] Received request from {client_ip} for {len(req.storyboard)} scenes")

    task_dir = TASKS_DIR / req.task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    try:
        image_paths = []
        for i, scene in enumerate(req.storyboard, 1):
            logger.info(f"\n--- Scene {i} ---")
            full_prompt = build_full_prompt(scene.dict())
            logger.info(f"Prompt: {full_prompt[:100]}...")
            filepath = generator.generate(prompt=full_prompt, output_dir=str(task_dir), counter=i)
            image_paths.append(Path(filepath).name)
        logger.info("All images generated!")
        return GenerateResponse(task_id=req.task_id, image_paths=image_paths)

    except Exception as e:
        error_msg = f"[{req.task_id}] Image generation error: {str(e)}"
        logger.error(error_msg)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/health")
async def health_check():
    import torch
    return {
        "status": "ok" if generator is not None else "failed",
        "gpu_available": torch.cuda.is_available(),
        "model": "stabilityai/sd-turbo"
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
    uvicorn.run(app="server:app", host="0.0.0.0", port=8002, log_level="info")
