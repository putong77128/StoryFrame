import os
import uuid
import edge_tts

class TTSGenerator:
    def __init__(self, output_root="server_tasks"):
        self.output_root = output_root
        os.makedirs(output_root, exist_ok=True)

    async def generate_audio_list(self, task_id: str, scenes: list, voice="zh-CN-XiaoxiaoNeural"):
        """
        scenes: [{ "id": 1, "narration": "xxx" }, ...]
        """
        task_dir = os.path.join(self.output_root, task_id)
        os.makedirs(task_dir, exist_ok=True)

        audio_filenames = []

        for i, scene in enumerate(scenes, start=1):
            text = scene.get("narration", "").strip()
            if not text:
                continue

            filename = f"{i:03d}.mp3"
            filepath = os.path.join(task_dir, filename)

            tts = edge_tts.Communicate(text, voice)
            await tts.save(filepath)

            audio_filenames.append(filename)

        return audio_filenames
