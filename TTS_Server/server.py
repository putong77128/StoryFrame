import os
import asyncio
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from generator_tts import TTSGenerator

app = FastAPI(
    title="TTS Audio Generator API",
    version="1.0"
)

TTS_ROOT = "server_tasks"
generator = TTSGenerator(output_root=TTS_ROOT)

class Scene(BaseModel):
    id: int
    narration: str

class GenerateRequest(BaseModel):
    task_id: str
    storyboard: list[Scene]

class GenerateResponse(BaseModel):
    task_id: str
    audio_paths: list[str]


@app.post("/generate/audio", response_model=GenerateResponse)
async def generate_audio(req: GenerateRequest):
    if not req.storyboard:
        raise HTTPException(400, "storyboard is empty")

    audio_paths = await generator.generate_audio_list(
        task_id=req.task_id,
        scenes=[s.dict() for s in req.storyboard]
    )

    return GenerateResponse(task_id=req.task_id, audio_paths=audio_paths)


@app.get("/download/{task_id}/{filename}")
async def download_audio(task_id: str, filename: str):
    file_path = Path(TTS_ROOT) / task_id / filename
    if not file_path.exists():
        raise HTTPException(404, "File not found")
    return FileResponse(file_path)
