import os
import requests
import time
import base64
from typing import Dict, Any


SERVER_URL = "http://localhost:8000"
TIMEOUT = 120
SAVE_IMAGES = True
TEST_OUTPUT_DIR = "./test_output"


def ensure_output_dir():
    if not os.path.exists(TEST_OUTPUT_DIR):
        os.makedirs(TEST_OUTPUT_DIR)


def test_health() -> bool:
    try:
        resp = requests.get(f"{SERVER_URL}/health", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print("Server status:")
            print(f"Text model: {data.get('text_model')}")
            print(f"Image model loaded: {data.get('image_model_loaded')}")
            print(f"Device: {data.get('device')}")
            return True
        else:
            print(f"Health check failed: HTTP {resp.status_code}")
            return False
    except Exception as e:
        print(f"Failed to connect to server: {e}")
        return False


def save_image(b64_str: str, prompt: str) -> str:
    if not b64_str:
        return ""
    # Generate safe filename
    name_part = "".join(c for c in prompt[:30] if c.isalnum() or c in (' ', '_')).strip()
    filename = f"{int(time.time())}_{name_part.replace(' ', '_')}.png"
    filepath = os.path.join(TEST_OUTPUT_DIR, filename)
    try:
        data = base64.b64decode(b64_str)
        with open(filepath, 'wb') as f:
            f.write(data)
        return filepath
    except Exception as e:
        print(f"Failed to save image: {e}")
        return ""


def run_test_case(idx: int, total: int, case: Dict[str, Any]) -> bool:
    print(f"\nTest case {idx}/{total}:")
    print(f"Message: {case['message']}")
    print(f"Generate image: {case['generate_image']}")

    start = time.time()
    try:
        resp = requests.post(f"{SERVER_URL}/chat", json=case, timeout=TIMEOUT)
        elapsed = time.time() - start

        if resp.status_code == 200:
            result = resp.json()
            proc_time = result.get("processing_time", 0)
            print(f"Status: success")
            print(f"Total time: {elapsed:.2f}s (server: {proc_time:.2f}s)")
            print(f"Reply: {result.get('reply', '')[:100]}...")

            if case["generate_image"]:
                img_path = result.get("image_path")
                b64_img = result.get("image_base64")
                if img_path:
                    print(f"Image path: {img_path}")
                    if b64_img and SAVE_IMAGES:
                        saved = save_image(b64_img, case["message"])
                        if saved:
                            print(f"Saved image: {saved}")
                else:
                    print("Image generation failed")
            return True
        else:
            print(f"Request failed: {resp.status_code} - {resp.text[:200]}")
            return False

    except requests.exceptions.Timeout:
        print("Request timed out")
        return False
    except Exception as e:
        print(f"Request error: {e}")
        return False


def list_images():
    print("\nListing generated images on server...")
    try:
        resp = requests.get(f"{SERVER_URL}/images", timeout=10)
        if resp.status_code == 200:
            images = resp.json().get("images", [])
            print(f"Found {len(images)} images")
            for img in images[:3]:
                print(f"{img['filename']} ({img['created_time']})")
        else:
            print(f"Failed to list images: {resp.status_code}")
    except Exception as e:
        print(f"Error listing images: {e}")


def main():
    print("Running AI service end-to-end test")
    print("-" * 50)

    ensure_output_dir()

    if not test_health():
        print("Server is not ready. Exiting.")
        return

    test_cases = [
        {"message": "描述一只可爱的熊猫在竹林里吃竹子", "generate_image": True},
        {"message": "描绘一个宁静的湖边小屋", "generate_image": True},
        {"message": "只是一个文本请求", "generate_image": False},
    ]

    passed = 0
    for i, case in enumerate(test_cases, 1):
        if run_test_case(i, len(test_cases), case):
            passed += 1
        time.sleep(1)

    list_images()

    print("\nSummary:")
    print(f"Passed: {passed}/{len(test_cases)}")
    if SAVE_IMAGES and passed > 0:
        print(f"Images saved to: {os.path.abspath(TEST_OUTPUT_DIR)}")


if __name__ == "__main__":
    main()
