import requests

BASE_URL = "http://localhost:9000"

def test_tts_bulk(task_id, scenes):
    resp = requests.post(f"{BASE_URL}/generate/audio", json={
        "task_id": task_id,
        "storyboard": scenes
    })

    print(resp.status_code, resp.json())

if __name__ == "__main__":
    test_tts_bulk("debug001", [
        {"id": 1, "narration": "今天我们来学习光合作用"},
        {"id": 2, "narration": "光合作用是植物制造能量的过程"}
    ])
