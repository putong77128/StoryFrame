import os
import asyncio
import edge_tts
from datetime import datetime
from pathlib import Path


def build_full_narration(scene: dict) -> str:
    narration = scene.get("narration", "").strip()
    if not narration:
        raise ValueError("Scene must contain 'narration'")
    return narration


class AudioGenerator:
    def __init__(self, voice="zh-CN-XiaoxiaoNeural", rate="+0%", volume="+0%"):
        self.voice = voice
        self.rate = rate
        self.volume = volume

    async def generate(self, text: str, output_dir: str, counter: int) -> str:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        filename = f"{counter:03d}_{datetime.now().strftime('%H%M%S')}.mp3"
        filepath = output_path / filename

        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            volume=self.volume
        )
        await communicate.save(str(filepath))
        return str(filepath)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def cleanup(self):
        pass


if __name__ == "__main__":
    MOCK_STORYBOARD_JSON = {
        "scenes": [
            {
                "scene_title": "Lost in the Rain",
                "narration": "一只小猫在雨中瑟瑟发抖，躲在纸箱下。",
                "prompt": {"role": "小猫", "environment": "城市雨夜小巷"}
            },
            {
                "scene_title": "Kind Stranger",
                "narration": "一位老人发现了它，轻轻蹲下身子。",
                "prompt": {"role": "慈祥老人", "environment": "安静的住宅街道"}
            }
        ]
    }

    test_dir = "./tts_output"
    os.makedirs(test_dir, exist_ok=True)

    async def main():
        try:
            tts_gen = AudioGenerator(voice="zh-CN-XiaoxiaoNeural")
            for i, scene in enumerate(MOCK_STORYBOARD_JSON["scenes"], 1):
                print(f"\n--- Scene {i} ---")
                full_text = build_full_narration(scene)
                print(f"Text: {full_text}")
                audio_path = await tts_gen.generate(
                    text=full_text,
                    output_dir=test_dir,
                    counter=i
                )
                print(f"Saved: {audio_path}")
            print("All audio generated!")
        except Exception as e:
            print(f"Error: {e}")

    asyncio.run(main())
