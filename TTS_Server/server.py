from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from generator_tts import TTSGenerator

app = FastAPI(title="TTS Server", version="1.0")

tts_generator = TTSGenerator()


class TTSRequest(BaseModel):
    text: str
    voice: str = "zh-CN-XiaoxiaoNeural"


@app.post("/tts")
async def tts_api(req: TTSRequest):
    try:
        audio_path = await tts_generator.synthesize(
            text=req.text,
            voice=req.voice
        )
        return {"audio_file": audio_path}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
