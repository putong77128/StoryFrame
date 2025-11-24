from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import edge_tts
import uuid
import os

app = FastAPI()

OUTPUT_DIR = "generated_audio"
os.makedirs(OUTPUT_DIR, exist_ok=True)

class TTSRequest(BaseModel):
    text: str
    voice: str = "zh-CN-XiaoxiaoNeural"  # 默认中文女声

@app.post("/api/tts")
async def tts(req: TTSRequest):
    try:
        output_path = os.path.join(OUTPUT_DIR, f"tts_{uuid.uuid4().hex}.mp3")

        tts = edge_tts.Communicate(req.text, req.voice)
        await tts.save(output_path)

        return {"audio_file": output_path}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
