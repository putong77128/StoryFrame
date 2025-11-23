# LLM Server 使用说明

## 1. 安装 Ollama
https://ollama.com/download

## 2. 下载安装模型
ollama pull gemma3:1b

## 3. 创建 Python 虚拟环境
python -m venv venv
.\venv\Scripts\activate

## 4. 安装依赖
pip install -r requirements.txt

## 5. 启动 FastAPI
uvicorn llm_server:app --host 0.0.0.0 --port 8000 --reload

## 6. 调用接口
POST http://localhost:8000/api/generate_storyboard
