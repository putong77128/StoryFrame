import requests
from pathlib import Path


BASE_URL = "http://localhost:8001"
LOCAL_TASKS_DIR = Path("./client_tasks")


def generate_and_save(story: str, style: str, task_id: str):
    payload = {"story": story, "style": style, "task_id": task_id}
    print("Sending request to server...")
    try:
        resp = requests.post(f"{BASE_URL}/generate/storyboard", json=payload)
        resp.raise_for_status()
        data = resp.json()
        task_id = data["task_id"]
        json_name = data["json_name"]
        print(f"success! task id: {task_id}")
        return task_id, json_name

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        if hasattr(e.response, 'text'):
            print(f"Server response: {e.response.text}")
    except KeyError as e:
        print(f"Unexpected response format: missing {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    return None


def download_json(task_id: str, json_name: str):
    task_dir = LOCAL_TASKS_DIR / task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    url = f"{BASE_URL}/download/{task_id}/{json_name}"
    local_path = task_dir / json_name
    print(f"Downloading {json_name}...")
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        with open(local_path, "wb") as f:
            f.write(resp.content)
        print(f"Saved to {local_path}")
    except Exception as e:
        print(f"Failed to download {json_name}: {e}")


if __name__ == "__main__":
    input_story = "一只小猫在雨夜中迷路，最终被一位老人收养。"
    input_style = "吉卜力工作室动画风格，温暖怀旧，柔和光影"
    MOCK_TASK_ID = "1235"
    return_id, filename = generate_and_save(input_story, input_style, MOCK_TASK_ID)
    download_json(return_id, filename)
