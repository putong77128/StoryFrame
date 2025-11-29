from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json

from generator_llm import LLMStoryboardGenerator

app = FastAPI(
    title="LLM Storyboard Server",
    description="使用 gemma3:1b + Ollama 生成分镜 JSON",
    version="1.0.0"
)

TASKS_DIR = Path("./tasks")
TASKS_DIR.mkdir(parents=True, exist_ok=True)

generator = LLMStoryboardGenerator(model="gemma3:1b", max_attempts=3)


class GenerateRequest(BaseModel):
    story: str
    style: str
    task_id: str


class GenerateResponse(BaseModel):
    task_id: str
    json_name: str


@app.post("/generate/storyboard", response_model=GenerateResponse)
def generate_storyboard(req: GenerateRequest):
    """
    根据故事 + 风格生成分镜，并以 task_id 归档到 tasks/<task_id>/storyboard.json
    """
    result = generator.generate(req.story, req.style)

    if result is None:
        raise HTTPException(status_code=500, detail="LLM 未能生成有效 JSON（多次重试失败）")

    task_dir = TASKS_DIR / req.task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    filename = "storyboard.json"
    file_path = task_dir / filename

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return GenerateResponse(task_id=req.task_id, json_name=filename)


@app.get("/download/{task_id}/{filename}")
def download_storyboard(task_id: str, filename: str):
    """
    按 task_id + filename 下载生成好的 JSON 文件
    """
    file_path = TASKS_DIR / task_id / filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")

    return json.loads(file_path.read_text(encoding="utf-8"))


@app.get("/health")
def health_check():
    return {"status": "ok", "model": "gemma3:1b"}
