import requests

BASE_URL = "http://localhost:8000"


def test_generate_storyboard():
    payload = {
        "story": "猩猩刷牙，白牙齿与黑皮肤对比鲜明",
        "style": "搞笑幽默的动画广告，色彩鲜明，生动有趣",
        "task_id": "debug_001"
    }

    resp = requests.post(f"{BASE_URL}/generate/storyboard", json=payload)
    print("POST /generate/storyboard status:", resp.status_code)
    print("response json:", resp.json())

    if resp.status_code != 200:
        return

    data = resp.json()
    task_id = data["task_id"]
    json_name = data["json_name"]

    download_resp = requests.get(f"{BASE_URL}/download/{task_id}/{json_name}")
    print("GET /download status:", download_resp.status_code)
    print("downloaded json:", download_resp.json())


if __name__ == "__main__":
    test_generate_storyboard()
