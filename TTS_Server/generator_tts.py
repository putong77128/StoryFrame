import os
from datetime import datetime
from pathlib import Path

import edge_tts


def build_full_narration(scene: dict) -> str:
    narration = (scene.get("narration") or "").strip()
    if not narration:
        raise ValueError("Scene must contain non-empty 'narration'")
    return narration


class TTSGenerator:

    def __init__(self, default_voice: str = "zh-CN-XiaoxiaoNeural",
                 rate: str = "+0%", volume: str = "+0%"):
        self.default_voice = default_voice
        self.rate = rate
        self.volume = volume

    async def generate(self, text: str, output_dir: str,
                       counter: int, voice: str | None = None) -> str:

        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{counter:03d}_{datetime.now().strftime('%H%M%S')}.mp3"
        filepath = out_dir / filename

        communicate = edge_tts.Communicate(
            text=text,
            voice=voice or self.default_voice,
            rate=self.rate,
            volume=self.volume,
        )
        await communicate.save(str(filepath))
        return str(filepath)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def cleanup(self):
        # edge-tts 本身是网络服务客户端，这里暂时不需要额外清理
        pass
