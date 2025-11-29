# client.py
import json
from pathlib import Path
from typing import List

import requests

BASE_URL = "http://localhost:9000"
LOCAL_TASKS_DIR = Path("./client_tasks")


def prepare_mock_storyboard(task_id: str, storyboard_data: dict):
    task_dir = LOCAL_TASKS_DIR / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    storyboard_path = task_dir / "storyboard.json"
    with open(storyboard_path, "w", encoding="utf-8") as f:
        json.dump(storyboard_data, f, indent=2, ensure_ascii=False)
    print(f"Mock storyboard saved to {storyboard_path}")


def generate_and_save(task_id: str, scenes: list, voice: str | None = None) -> List[str] | None:
    payload = {"task_id": task_id, "storyboard": scenes}
    if voice is not None:
        payload["voice"] = voice

    print(f"Sending request to TTS server for task id: {task_id}")
    try:
        resp = requests.post(f"{BASE_URL}/generate/audio", json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return_task_id = data["task_id"]
        audio_paths = data["audio_paths"]
        print(f"success! returned task id: {return_task_id}")
        print(f"total {len(audio_paths)} audios")
        return audio_paths

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Server response: {e.response.text}")
    except KeyError as e:
        print(f"Unexpected response format: missing {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    return None


def download_audios(task_id: str, audio_paths: List[str]):
    task_dir = LOCAL_TASKS_DIR / task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    for filename in audio_paths:
        url = f"{BASE_URL}/download/{task_id}/{filename}"
        local_path = task_dir / filename
        print(f"Downloading {filename}...")
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            with open(local_path, "wb") as f:
                f.write(resp.content)
            print(f"Saved to {local_path}")
        except Exception as e:
            print(f"Failed to download {filename}: {e}")


if __name__ == "__main__":
    MOCK_TASK_ID = "demo_001"
    MOCK_STORYBOARD_JSON = {
        "scenes": [
            {
                "scene_title": "场景1：猩猩刷牙",
                "narration": "一只猩猩站在浴室的镜子前，认真地刷着牙。",
                "bgm_suggestion": "轻快的钢琴背景音乐",
                "prompt": {
                    "role": "一只可爱的猩猩",
                    "environment": "明亮的浴室，带有大镜子",
                    "light": "柔和的顶部灯光",
                    "style": "cartoon, bright colors",
                },
            },
            {
                "scene_title": "场景2：露出洁白的牙齿",
                "narration": "刷完牙后，猩猩对着镜子咧嘴一笑，露出一口洁白的牙齿。",
                "bgm_suggestion": "欢快上扬的短音效",
                "prompt": {
                    "role": "微笑的猩猩特写",
                    "environment": "镜子前的特写画面",
                    "light": "高亮度打光，突出牙齿",
                    "style": "advertising shot, high key lighting",
                },
            },
        ]
    }

    prepare_mock_storyboard(MOCK_TASK_ID, MOCK_STORYBOARD_JSON)
    paths = generate_and_save(MOCK_TASK_ID, MOCK_STORYBOARD_JSON["scenes"],
                              voice="zh-CN-XiaoxiaoNeural")
    if paths:
        download_audios(MOCK_TASK_ID, paths)
