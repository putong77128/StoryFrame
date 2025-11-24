import json
import logging
import traceback
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel as PydanticBaseModel
from generate_words import StoryboardGenerator


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Storyboard Generator API",
    description="Generate storyboards and retrieve via task_id",
    version="1.0"
)

TASKS_DIR = Path("./server_tasks")
TASKS_DIR.mkdir(exist_ok=True)
generator = StoryboardGenerator(model_name="qwen2.5:0.5b", temperature=0.4, max_attempts=3)


class GenerateRequest(PydanticBaseModel):
    story: str
    style: str
    task_id: str


class GenerateResponse(PydanticBaseModel):
    task_id: str
    json_name: str


@app.post("/generate/storyboard", response_model=GenerateResponse)
async def generate_storyboard(request: Request, req: GenerateRequest):
    client_ip = request.client.host if request.client else "unknown"
    raw_body = await request.body()
    logger.info(f"from ip: {client_ip}")
    logger.info(f"raw request: {raw_body.decode('utf-8', errors='replace')}")
    logger.info(f"after decode: story='{req.story}', style='{req.style}'")

    try:
        result = generator.generate(story=req.story, style=req.style)
        if not result:
            raise ValueError("Storyboard generation returned None or empty")

        task_id = req.task_id
        task_dir = TASKS_DIR / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        filename = "storyboard.json"
        result_path = task_dir / filename
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result.dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"Task {task_id} completed")
        logger.info(f"file saved to {result_path}")
        return GenerateResponse(task_id=task_id, json_name=filename)

    except Exception as e:
        error_msg = f"Generation storyboard failed: {str(e)}"
        logger.error(error_msg)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/health")
async def health_check():
    return {"status": "ok", "model": "qwen2.5:0.5b"}


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
    uvicorn.run(app="server:app", host="0.0.0.0", port=8001, log_level="info")
