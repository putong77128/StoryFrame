import os
import uuid
import edge_tts


class TTSGenerator:
    def __init__(self, output_dir="generated_audio"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    async def synthesize(self, text: str, voice: str = "zh-CN-XiaoxiaoNeural") -> str:
        """
        生成语音文件并返回文件路径
        """
        filename = f"tts_{uuid.uuid4().hex}.mp3"
        output_path = os.path.join(self.output_dir, filename)

        tts = edge_tts.Communicate(text, voice)
        await tts.save(output_path)

        return output_path
