import os
import torch
import logging
from datetime import datetime
from diffusers import AutoPipelineForText2Image


logging.getLogger("diffusers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)


class ImageGenerator:
    def __init__(self, model_name="stabilityai/sd-turbo", cache_dir="F:\\huggingface\\models"):
        if torch.cuda.is_available():
            self.pipe = AutoPipelineForText2Image.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
                variant="fp16",
                cache_dir=cache_dir,
                local_files_only=True
            ).to("cuda")
        else:
            raise RuntimeError("need GPU")

    def generate(self, prompt: str, output_dir: str, counter: int, width=512, height=512) -> str:
        image = self.pipe(prompt=prompt, num_inference_steps=4,
                          guidance_scale=0.0, width=width, height=height).images[0]
        filename = f"{counter:03d}_{datetime.now().strftime('%H%M%S')}.png"
        filepath = os.path.join(output_dir, filename)
        image.save(filepath)
        return filepath


def build_full_prompt(scene: dict) -> str:
    parts = [scene.get("narration", "").strip()]
    prompt_dict = scene.get("prompt", {})

    for key in ["role", "environment", "light"]:
        value = prompt_dict.get(key, "").strip()
        if value and value.lower() not in parts[-1].lower():
            parts.append(value)

    style = prompt_dict.get("style", "Studio Ghibli animation style").strip()
    parts += [style, "masterpiece, best quality, high detail"]

    return ", ".join(filter(None, parts))


if __name__ == "__main__":
    MOCK_STORYBOARD_JSON = {
        "scenes": [
            {
                "scene_title": "Lost in the Rain",
                "narration": "A small kitten shivers under a cardboard box.",
                "bgm_suggestion": "Gentle piano with rain sounds",
                "prompt": {
                    "role": "a small wet kitten",
                    "environment": "dark rainy alley in a city",
                    "light": "dim yellow streetlights reflecting on puddles",
                    "style": "Studio Ghibli animation style"
                }
            },
            {
                "scene_title": "Kind Stranger",
                "narration": "An old man notices the kitten and kneels down gently.",
                "bgm_suggestion": "Warm strings with hopeful melody",
                "prompt": {
                    "role": "an elderly man with kind eyes and an umbrella",
                    "environment": "quiet neighborhood street at night, light rain",
                    "light": "soft warm light from nearby windows",
                    "style": "Studio Ghibli animation style"
                }
            }
        ]
    }

    test_dir = "./test"
    os.makedirs(test_dir, exist_ok=True)
    try:
        generator = ImageGenerator()
        for i, scene_json in enumerate(MOCK_STORYBOARD_JSON["scenes"], 1):
            print(f"\n--- Scene {i} ---")
            full_prompt = build_full_prompt(scene_json)
            print(f"Prompt: {full_prompt[:100]}...")
            generator.generate(prompt=full_prompt, output_dir=test_dir, counter=1)
        print("All images generated!")
    except Exception as e:
        print(f"Error: {e}")
