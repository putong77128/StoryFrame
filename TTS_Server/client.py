import requests

BASE_URL = "http://localhost:9000/tts"


def test_tts(text, voice="zh-CN-XiaoxiaoNeural"):
    payload = {"text": text, "voice": voice}
    resp = requests.post(BASE_URL, json=payload)

    print("Status:", resp.status_code)
    print("Response:", resp.json())


if __name__ == "__main__":
    test_tts("好望角发现了，为什么死海里千帆相竞")
