import os
import uuid
import base64
import torch
import logging
from datetime import datetime
from diffusers import AutoPipelineForText2Image
from huggingface_hub import snapshot_download

logger = logging.getLogger(__name__)


class ImageGenerator:
    def __init__(self, model_name: str = "stabilityai/sd-turbo", cache_dir: str = "F:\\huggingface\\models"):
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.output_dir = "generated_images"
        self.pipe = None
        self._initialize_model()

    def _initialize_model(self):
        try:
            logger.info(f"load image model: {self.model_name}")
            os.makedirs(self.output_dir, exist_ok=True)

            # 尝试仅使用本地缓存
            use_local_files = False
            try:
                snapshot_download(
                    self.model_name,
                    cache_dir=self.cache_dir,
                    local_files_only=True
                )
                use_local_files = True
                logger.info("offline loading")
            except Exception as e:
                logger.warning(f"no cache: {e}")

            # 根据设备选择精度和设备
            if torch.cuda.is_available():
                logger.info("GPU setting")
                self.pipe = AutoPipelineForText2Image.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16,
                    variant="fp16",
                    cache_dir=self.cache_dir,
                    local_files_only=use_local_files
                ).to("cuda")
            else:
                logger.info("CPU setting")
                self.pipe = AutoPipelineForText2Image.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float32,
                    cache_dir=self.cache_dir,
                    local_files_only=use_local_files
                ).to("cpu")

            logger.info("load image model success")

        except Exception as e:
            logger.error(f"load image model error: {e}")
            self.pipe = None

    def is_available(self) -> bool:
        return self.pipe is not None

    def generate_image(self, prompt: str) -> str:
        if not self.is_available():
            raise RuntimeError("load image model error")

        logger.info(f"start generate image，prompt: {prompt[:80]}...")

        # 生成图像
        if torch.cuda.is_available():
            with torch.autocast("cuda"):
                image = self.pipe(
                    prompt=prompt,
                    num_inference_steps=4,
                    guidance_scale=0.0,
                    width=512,
                    height=512
                ).images[0]
        else:
            image = self.pipe(
                prompt=prompt,
                num_inference_steps=4,
                guidance_scale=0.0,
                width=512,
                height=512
            ).images[0]

        # 保存
        filename = f"{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.output_dir, filename)
        image.save(filepath)
        logger.info(f"image saved: {filepath}")
        return filepath

    @staticmethod
    def image_to_base64(image_path: str) -> str:
        try:
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            logger.error(f"image to base64 failed: {e}")
            return str(None)

    def get_image_count(self) -> int:
        try:
            return len([
                f for f in os.listdir(self.output_dir)
                if f.lower().endswith(('.png', '.jpg', '.jpeg'))
            ])
        except (FileNotFoundError, PermissionError, OSError):
            return 0
