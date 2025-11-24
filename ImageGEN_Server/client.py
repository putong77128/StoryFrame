import json
import requests
from typing import List
from pathlib import Path


BASE_URL = "http://localhost:8002"
LOCAL_TASKS_DIR = Path("./client_tasks")


def prepare_mock_storyboard(task_id: str, storyboard_data: dict):
    task_dir = LOCAL_TASKS_DIR / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    storyboard_path = task_dir / "storyboard.json"
    with open(storyboard_path, "w", encoding="utf-8") as f:
        json.dump(storyboard_data, f, indent=2, ensure_ascii=False)
    print(f"Mock storyboard saved to {storyboard_path}")


def generate_and_save(task_id: str, scenes: list):
    payload = {"task_id": task_id, "storyboard": scenes}
    print(f"Sending request to server for task id: {task_id}")
    try:
        resp = requests.post(f"{BASE_URL}/generate/images", json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return_task_id = data["task_id"]
        image_paths = data["image_paths"]
        print(f"success! returned task id: {return_task_id}")
        print(f"total {len(image_paths)} images")
        return image_paths

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        if hasattr(e.response, 'text'):
            print(f"Server response: {e.response.text}")
    except KeyError as e:
        print(f"Unexpected response format: missing {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    return None


def download_images(task_id: str, image_paths: List[str]):
    task_dir = LOCAL_TASKS_DIR / task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    for filename in image_paths:
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
    MOCK_TASK_ID = "1235"
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
    prepare_mock_storyboard(MOCK_TASK_ID, MOCK_STORYBOARD_JSON)
    return_image_paths = generate_and_save(MOCK_TASK_ID, MOCK_STORYBOARD_JSON["scenes"])
    download_images(MOCK_TASK_ID, return_image_paths)
