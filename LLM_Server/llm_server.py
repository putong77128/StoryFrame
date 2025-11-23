from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import json
import re

app = FastAPI()

OLLAMA_URL = "http://localhost:11434/api/chat"

class StoryRequest(BaseModel):
    story_text: str
    style: str   # 电影 / 动画 / 写实

class StoryboardResponse(BaseModel):
    storyboard_json: dict


SYSTEM_PROMPT = """
你是一个专业的影视分镜脚本生成助手。
请严格生成结构化、多镜头、电影风格的分镜 JSON。
禁止任何非 JSON 内容（不要输出解释、不要输出 markdown、不要输出中文说明文字）。

JSON 输出格式如下（必须完全符合此结构）：

{
  "title": "故事标题",
  "style": "电影",
  "scenes": [
    {
      "scene_title": "场景标题",
      "shots": [
        {
          "id": 1,
          "prompt": "英文画面描述（文生图用，必须详细）",
          "narration": "旁白文案",
          "bgm_suggestion": "BGM 建议"
        }
      ]
    }
  ]
}

要求：
1. 必须生成 1 个 scene,只生成 1 个scene。
2. scene 中必须生成 3-6 个 shots，不能少于 3 个，不能多于 6 个。
3. 所有英文 prompt 必须详细，包含镜头类型、景别、光线、氛围（用于文生图）。
4. narration 必须是中文，适合视频旁白风格。
5. bgm_suggestion 给出合理的电影级配乐建议。
6. 严格返回 JSON，不能有任何非 JSON 文本。
"""


def clean_json_string(raw: str):
    """清洗 LLM 输出以确保可以正常 json.loads"""

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
        raw = raw[:json_end+1]

    raw = re.sub(r"[\x00-\x1F\x7F]", "", raw)

    return raw.strip()


@app.post("/api/generate_storyboard", response_model=StoryboardResponse)
def generate_storyboard(req: StoryRequest):
    prompt = f"""
    请根据以下故事生成结构化、多镜头的电影分镜 JSON。

    风格：{req.style}
    故事内容：{req.story_text}

    请生成 3-6 个镜头，并完全符合上方 JSON 结构。
    只输出 JSON。
    """

    payload = {
        "model": "gemma3:1b",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }

    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()

        raw_content = data["message"]["content"]
        cleaned = clean_json_string(raw_content)

        storyboard = json.loads(cleaned)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM JSON 解析失败: {str(e)}")

    return {"storyboard_json": storyboard}
