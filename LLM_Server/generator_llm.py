import json
import re
import requests

# 本地 Ollama 服务地址
OLLAMA_URL = "http://localhost:11434/api/chat"


class LLMStoryboardGenerator:
    """
    封装调用 Ollama + gemma3:1b 的分镜生成器
    使用你已经验证过的 SYSTEM_PROMPT 和清洗逻辑
    """

    def __init__(self, model: str = "gemma3:1b", max_attempts: int = 3):
        self.model = model
        self.max_attempts = max_attempts

        # —— 这里就是你原来的 SYSTEM_PROMPT，完整保留 —— #
        self.system_prompt = """
You are a professional storyboard generation assistant.

Your ONLY job is to output a structured JSON storyboard.
All content MUST follow these rules:

1. All "prompt" fields MUST be in **pure English only**.
2. No Chinese characters are allowed inside "prompt".
3. "narration" MUST be in Chinese.
4. "bgm_suggestion" must be short and in Chinese or English depending on natural fit.
5. Json must contain:
   - title: string
   - style: string (copy user's style or simplified English version)
   - scenes: array
   - Each scene contains 3–6 shots
   - Each shot contains:
       id (int)
       prompt (English)
       narration (Chinese)
       bgm_suggestion (string)
6. You MUST ALWAYS output ONLY JSON. No explanations, no markdown.

You are allowed to convert ANY user style (regardless of whether it is a phrase or full Chinese sentence)
into an *English-friendly film style description* inside the English "prompt".
But the "style" field in JSON should keep the user's original text.

STRICT REQUIREMENTS:
- Zero Chinese inside any "prompt".
- JSON must be valid, no trailing commas, no comments.
"""

    # 清洗 LLM 输出，复用你原来的逻辑
    def _clean_json_string(self, raw: str) -> str:
        # 去掉 ```json 或 ```
        raw = re.sub(r"```json", "", raw)
        raw = re.sub(r"```", "", raw)

        # 去掉开头非 { 的部分
        json_start = raw.find("{")
        if json_start != -1:
            raw = raw[json_start:]

        # 去掉最后一个 } 后的内容
        json_end = raw.rfind("}")
        if json_end != -1:
            raw = raw[:json_end + 1]

        # 去掉控制字符
        raw = re.sub(r"[\x00-\x1F\x7F]", "", raw)

        return raw.strip()

    def generate(self, story_text: str, style: str):
        """
        调用 Ollama + gemma3:1b 生成分镜 JSON
        成功返回一个 Python dict（已经 json.loads）
        失败返回 None
        """

        user_prompt = f"""
Generate a storyboard based on the following story and style.

Story (Chinese allowed): {story_text}
Style (Chinese allowed): {style}

IMPORTANT:
- Convert the style into an ENGLISH visual style only for the "prompt" fields.
- All prompts must be detailed English descriptions of shots.
- narration must be Chinese.

Output 3–6 shots total.
Return ONLY JSON.
"""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False
        }

        for attempt in range(1, self.max_attempts + 1):
            try:
                print(f"[LLM] 尝试第 {attempt} 次调用 Ollama...")
                resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
                resp.raise_for_status()
                data = resp.json()

                raw_content = data["message"]["content"]
                print("===== RAW OUTPUT START =====")
                print(raw_content)
                print("===== RAW OUTPUT END =====")

                cleaned = self._clean_json_string(raw_content)
                storyboard = json.loads(cleaned)
                return storyboard

            except Exception as e:
                print(f"[LLM] 第 {attempt} 次解析失败: {e}")

        # 所有重试失败，返回 None
        return None
