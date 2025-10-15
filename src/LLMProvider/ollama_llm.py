from ..helpers.Config import get_settings
from langchain_ollama import ChatOllama

config = get_settings()
ollama_model_name = config.OLLAMA_MODEL_NAME
ollama_url = config.OLLAMA_URL
temperature = config.TEMPERATURE

llm = ChatOllama(model=ollama_model_name, ollama_url=ollama_url, temperature=temperature)
print(llm.invoke("Hello, how are you?"))
