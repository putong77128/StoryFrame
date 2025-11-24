import re
import json
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from langchain_ollama import OllamaLLM


def contains_chinese(text: str) -> bool:
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def check_no_chinese(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            check_no_chinese(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            check_no_chinese(item, f"{path}[{i}]")
    elif isinstance(obj, str) and contains_chinese(obj):
        raise ValueError(f"Chinese detected at '{path}'")


class Scene(BaseModel):
    scene_title: str = Field(description="Scene title in English")
    narration: str = Field(description="Narration in English")
    bgm_suggestion: str = Field(description="BGM suggestion in English")
    prompt: dict = Field(description='Must contain "role", "environment", "light", "style", all in English')


class Storyboard(BaseModel):
    scenes: List[Scene] = Field(description="A list of 4 to 5 scenes")

    @validator("scenes")
    def validate_scene_count(cls, v):
        if not (4 <= len(v) <= 5):
            raise ValueError("Must have 4–5 scenes")
        return v


class StoryboardGenerator:
    def __init__(self, model_name: str = "qwen2.5:0.5b",
                 temperature: float = 0.4, max_attempts: int = 3):
        self.llm = OllamaLLM(model=model_name, temperature=temperature)
        self.max_attempts = max_attempts

    def generate(self, story: str, style: str) -> Optional[Storyboard]:
        """
        根据故事和艺术风格生成英文分镜脚本
        Args:
            story: 故事描述
            style: 艺术风格描述
        Returns:
            成功时返回 Storyboard 对象，失败返回 None
        """
        prompt = f"""
        You are a professional storyboard writer.
        
        Story (for context): {story}
        Art Style: {style}
        
        Generate a storyboard with 4 to 5 scenes. Output ONLY a valid JSON object with a "scenes" array.
        
        Each scene must have:
        - "scene_title": in English
        - "narration": in English
        - "bgm_suggestion": in English
        - "prompt": an object with "role", "environment", "light", "style" (all in English)
        
        Example structure:
        {{
          "scenes": [
            {{
              "scene_title": "...",
              "narration": "...",
              "bgm_suggestion": "...",
              "prompt": {{
                "role": "...",
                "environment": "...",
                "light": "...",
                "style": "Studio Ghibli animation style"
              }}
            }}
          ]
        }}
        
        IMPORTANT:
        - All text MUST be in English.
        - NO CHINESE CHARACTERS WHATSOEVER.
        - Output ONLY JSON. No explanations.
        """

        for attempt in range(self.max_attempts):
            try:
                print(f"Attempt {attempt + 1}...")
                raw = self.llm.invoke(prompt).strip()

                # JSON部分
                match = re.search(r"\{.*\}", raw, re.DOTALL)
                if not match:
                    raise ValueError("No JSON object found in response")

                data = json.loads(match.group())
                check_no_chinese(data)
                result = Storyboard(**data)
                print("Success: Valid English-only storyboard generated!")
                return result

            except (json.JSONDecodeError, ValueError) as e:
                print(f"JSON error: {e}")
            except Exception as e:
                print(f"Unexpected error: {e}")

        print("All attempts failed. Could not generate valid storyboard.")
        return None


if __name__ == "__main__":
    generator = StoryboardGenerator(model_name="qwen2.5:0.5b", temperature=0.4)

    input_story = "一只小猫在雨夜中迷路，最终被一位老人收养。"
    input_style = "吉卜力工作室动画风格，温暖怀旧，柔和光影"

    output_result = generator.generate(story=input_story, style=input_style)

    if output_result:
        output_json_str = json.dumps(output_result.dict(), indent=2, ensure_ascii=False)
        print("\n" + "=" * 60)
        # print("Final JSON to send to client (first 200 chars):")
        # print(repr(output_json_str[:200]))
        # print("\nActual readable output:")
        print(output_json_str)
    else:
        print("\nFailed to generate storyboard after all retries.")
