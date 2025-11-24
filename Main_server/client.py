import time
import requests
from pathlib import Path

'''
TASK_STATUS[task_id] = {
    "status": "queued",
    "story": req.story,
    "style": req.style,
    "storyboard_file": None,
    "images": [],
    "error": None
}
'''


BASE_URL = "http://localhost:8000"
LOCAL_TASKS_DIR = Path("./client_test")


def start_pipeline(story: str, style: str):
    print("Starting pipeline")
    resp = requests.post(f"{BASE_URL}/start_pipeline/", json={"story": story, "style": style})
    resp.raise_for_status()
    task_id = resp.json()["task_id"]
    print(f"Task started: {task_id}")
    task_dir = LOCAL_TASKS_DIR / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    storyboard_downloaded = False
    images_downloaded = False
    status_data = {"status": "unknown"}

    while True:
        status_resp = requests.get(f"{BASE_URL}/status/{task_id}")
        if status_resp.status_code == 404:
            print("Task not found")
            break
        status_data = status_resp.json()
        current_status = status_data["status"]
        print(f"Status: {current_status}")

        # if not storyboard_downloaded and current_status == "storyboard_ready":
        if not storyboard_downloaded:
            filename = status_data["storyboard_file"]
            if filename:
                print(f"Downloading storyboard: {filename}")
                r = requests.get(f"{BASE_URL}/download/{task_id}/{filename}")
                r.raise_for_status()
                local_path = task_dir / filename
                local_path.write_bytes(r.content)
                print(f"Saved to {local_path}")
                storyboard_downloaded = True

        if not images_downloaded and current_status == "completed":
            image_files = status_data["images"]
            print(f"Downloading {len(image_files)} images...")
            for img in image_files:
                r = requests.get(f"{BASE_URL}/download/{task_id}/{img}")
                r.raise_for_status()
                (LOCAL_TASKS_DIR / task_id / img).write_bytes(r.content)
            images_downloaded = True

        if current_status in ("completed", "failed"):
            break

        time.sleep(3)

    if status_data["status"] == "completed":
        print("All done! Files saved")
    elif status_data["status"] == "failed":
        print(f"Pipeline failed: {status_data.get('error', 'Unknown error')}")
    elif status_data["status"] == "unknown":
        print(f"no status response")


if __name__ == "__main__":
    input_story = "一只小猫在雨夜中迷路，最终被一位老人收养。"
    input_style = "吉卜力工作室动画风格，温暖怀旧，柔和光影"
    start_pipeline(input_story, input_style)
