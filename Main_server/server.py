import uuid
import json
import asyncio
import logging
import requests
from pathlib import Path
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Main Server API",
    description="whole pipeline",
    version="1.0"
)

# 所有子服务端口
STORYBOARD_SERVICE_URL = "http://localhost:8001"
IMAGE_SERVICE_URL = "http://localhost:8002"

PIPELINE_DIR = Path("./pipeline_tasks")
PIPELINE_DIR.mkdir(exist_ok=True)
# 仅用于demo
TASK_STATUS = {}


class PipelineRequest(BaseModel):
    story: str
    style: str


@app.post("/start_pipeline/")
async def start_pipeline(request: Request, req: PipelineRequest):
    client_ip = request.client.host if request.client else "unknown"
    raw_body = await request.body()
    logger.info(f"from ip: {client_ip}")
    logger.info(f"raw request: {raw_body.decode('utf-8', errors='replace')}")
    logger.info(f"after decode: story='{req.story}', style='{req.style}'")

    task_id = str(uuid.uuid4())
    task_dir = PIPELINE_DIR / task_id
    task_dir.mkdir(exist_ok=True)

    TASK_STATUS[task_id] = {
        "status": "queued",
        "story": req.story,
        "style": req.style,
        "storyboard_file": None,
        "images": [],
        "error": None
    }

    # noinspection PyAsyncCall
    asyncio.create_task(run_pipeline_async(task_id, req.story, req.style))
    return {"task_id": task_id, "status": "queued"}


def generate_storyboard(story: str, style: str, task_id: str):
    resp = requests.post(
        f"{STORYBOARD_SERVICE_URL}/generate/storyboard",
        json={"story": story, "style": style, "task_id": task_id}
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Failed to generate storyboard")
    data = resp.json()
    return data["task_id"], data["json_name"]


def download_storyboard(task_id: str, filename: str):
    resp = requests.get(f"{STORYBOARD_SERVICE_URL}/download/{task_id}/{filename}")
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Failed to download storyboard")
    storyboard = resp.json()
    output_path = PIPELINE_DIR / task_id / filename
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(storyboard, f, indent=2, ensure_ascii=False)
    return storyboard


def process_storyboard(storyboard: dict) -> list:
    scenes = storyboard.get("scenes", [])
    return scenes


def generate_images(task_id: str, scenes: list):
    resp = requests.post(
        f"{IMAGE_SERVICE_URL}/generate/images",
        json={
            "task_id": task_id,
            "storyboard": scenes
        }
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Failed to generate images")
    data = resp.json()
    return data["image_paths"]


def download_images(task_id: str, image_paths: list):
    for img_name in image_paths:
        resp = requests.get(f"{IMAGE_SERVICE_URL}/download/{task_id}/{img_name}")
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Failed to download images")
        save_path = PIPELINE_DIR / task_id / img_name
        with open(save_path, "wb") as f:
            f.write(resp.content)


async def run_pipeline_async(task_id: str, story: str, style: str):
    try:
        # Step 1
        TASK_STATUS[task_id]["status"] = "generating_storyboard"
        _, json_name = generate_storyboard(story, style, task_id)
        storyboard = download_storyboard(task_id, json_name)
        TASK_STATUS[task_id].update({
            "status": "storyboard_ready",
            "storyboard_file": json_name
        })

        # Step 2
        TASK_STATUS[task_id]["status"] = "generating_images"
        scenes = process_storyboard(storyboard)
        image_paths = generate_images(task_id, scenes)
        download_images(task_id, image_paths)
        TASK_STATUS[task_id].update({
            "status": "completed",
            "images": image_paths
        })

    except Exception as e:
        logger.exception(f"[{task_id}] Pipeline failed")
        TASK_STATUS[task_id].update({
            "status": "failed",
            "error": str(e)
        })


@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    if task_id not in TASK_STATUS:
        raise HTTPException(404, "Task not found")
    return TASK_STATUS[task_id]


@app.get("/health")
async def health_check():
    return {"status": "ok", "llm_model": "qwen2.5:0.5b",
            "img_model": "stabilityai/sd-turbo"}


@app.get("/download/{task_id}/{filename}")
def download_file(task_id: str, filename: str):
    file_path = PIPELINE_DIR.resolve() / task_id / filename
    try:
        file_path.relative_to(PIPELINE_DIR.resolve())
    except ValueError:
        raise HTTPException(403, "Access denied")
    if not file_path.is_file():
        raise HTTPException(404, "File not found")
    return FileResponse(file_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
