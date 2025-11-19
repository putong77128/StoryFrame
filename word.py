import logging
from langchain_ollama import OllamaLLM

logger = logging.getLogger(__name__)


class TextGenerator:
    def __init__(self, model_name: str = "qwen2.5:0.5b"):
        self.model_name = model_name
        self.llm = None
        self._initialize_model()

    def _initialize_model(self):
        try:
            logger.info(f"load text model: {self.model_name}")
            self.llm = OllamaLLM(model=self.model_name)
            logger.info("load text model success")
        except Exception as e:
            logger.error(f"load text model error: {e}")
            raise

    def generate_reply(self, message: str) -> str:
        if not self.llm:
            raise RuntimeError("reply text error")

        logger.info(f"text input: {message[:100]}...")
        reply = self.llm.invoke(message)
        logger.info(f"reply output: {reply[:100]}...")
        return reply
