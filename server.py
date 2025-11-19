import warnings
warnings.filterwarnings("ignore", category=UserWarning, message=".*pydantic.*")
warnings.filterwarnings("ignore", message=".*torch_dtype.*deprecated.*")
import os
import torch
import logging
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from word import TextGenerator
from picture import ImageGenerator


# log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("init text model")  # langchain调用ollama
text_generator = TextGenerator(model_name="qwen2.5:0.5b")
logger.info("init image model")  # diffusers调用
image_generator = ImageGenerator(model_name="stabilityai/sd-turbo",)

# server config
app = FastAPI(title="文本与图片生成服务器")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)  # type: ignore


class ChatRequest(BaseModel):
    message: str
    generate_image: bool = True


class ChatResponse(BaseModel):
    reply: str
    image_path: Optional[str] = None
    image_base64: Optional[str] = None
    success: bool = True
    message: str = ""
    processing_time: float = 0.0


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    start_time = datetime.now()
    logger.info(f"get post: {req.message[:100]}")

    try:
        # 1. 文本生成
        llm_reply = text_generator.generate_reply(req.message)

        # 2. 图像生成
        image_path = None
        image_base64 = None
        if req.generate_image and image_generator.is_available():
            try:
                image_path = image_generator.generate_image(llm_reply)
                image_base64 = image_generator.image_to_base64(image_path)
            except Exception as e:
                logger.error(f"image_generator error: {e}")

        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"done. take: {processing_time:.2f} s")

        return ChatResponse(
            reply=llm_reply,
            image_path=image_path,
            image_base64=image_base64,
            success=True,
            message="success",
            processing_time=processing_time
        )

    except Exception as e:
        logger.exception("post error")
        return ChatResponse(
            reply="",
            success=False,
            message=f"post error: {str(e)}",
            processing_time=(datetime.now() - start_time).total_seconds()
        )


@app.get("/image/{filename}")
async def get_image(filename: str):
    safe_name = os.path.basename(filename)
    filepath = os.path.join("generated_images", safe_name)
    if os.path.isfile(filepath):
        return FileResponse(filepath)
    return {"error": "picture are not exited"}


@app.get("/images")
async def list_images():
    folder = "generated_images"
    if not os.path.exists(folder):
        return {"images": []}
    images = []
    for f in os.listdir(folder):
        if f.lower().endswith(('.png', '.jpg', '.jpeg')):
            path = os.path.join(folder, f)
            images.append({
                "filename": f,
                "url": f"/image/{f}",
                "created_time": datetime.fromtimestamp(os.path.getctime(path)).strftime("%Y-%m-%d %H:%M:%S"),
                "size_bytes": os.path.getsize(path)
            })
    return {"images": sorted(images, key=lambda x: x["created_time"], reverse=True)}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "text_model": text_generator.model_name,
        "image_model": image_generator.model_name,
        "image_model_loaded": image_generator.is_available(),
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "images_generated": image_generator.get_image_count()
    }


@app.get("/")
async def root():
    return {
        "service": "文本与图片生成服务器",
        "endpoints": ["/chat", "/images", "/image/{filename}", "/health"]
    }


if __name__ == "__main__":
    logger.info("start server at http://localhost:8000")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
