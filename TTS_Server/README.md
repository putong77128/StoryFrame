# 🎤 TTS Server (Edge-TTS Version)

本目录为 StoryFrame 项目中的 **文本转语音（TTS）服务**  
采用 **FastAPI + Microsoft Edge-TTS** 实现，具有 **轻量、高效、安装简单** 的特点。

---

## 🚀 功能简介

TTS 服务用于将文字旁白转换为音频文件，供视频生成流程使用。

### 功能包括：

- 输入文本 → 输出 MP3 语音文件  
- 支持多种中文语音（微软自然语音，如 Xiaoxiao、Yunxi 等）  
- 生成速度快，无需 GPU  
- 生成的音频保存在 `generated_audio/` 目录下  
- 可直接通过 HTTP API 调用，便于 Android 端集成  

---

## 🧩 技术栈

| 模块 | 技术 |
|------|------|
| 服务框架 | FastAPI |
| 语音生成 | Edge-TTS（微软在线 TTS） |
| 运行方式 | Python 3.10+ |
| 部署环境 | WSL / Linux / Windows 任意环境 |

无需下载大模型，无需显卡，极为轻量。

---

## 📦 依赖安装

进入虚拟环境：

```bash

source venv/bin/activate
安装依赖：

pip install -r requirements.txt


当前项目依赖：

edge-tts
fastapi
uvicorn

▶️ 启动服务
uvicorn server_tts:app --host 0.0.0.0 --port 9000 --reload


启动成功后访问：

👉 http://localhost:9000/docs

即可看到 Swagger API 文档。

📝 API 使用说明
POST /api/tts

将输入文本转换为 MP3 语音文件。

请求示例：
{
  "text": "你好，我是故事生成项目的语音服务。",
  "voice": "zh-CN-XiaoxiaoNeural"
}

返回示例：
{
  "audio_file": "generated_audio/tts_3c91f09e0f3e4e93a99dff34c915e93f.mp3"
}


生成的音频会保存在：

generated_audio/

🔊 可选语音列表（部分）
语音名称	风格	说明
zh-CN-XiaoxiaoNeural	甜美女声	默认，适合旁白
zh-CN-YunxiNeural	男声	稳重、正式
zh-CN-XiaoyiNeural	女声	明亮、有青春感
zh-CN-YunjianNeural	男声	低沉磁性