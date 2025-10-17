

from typing import List, Dict, Any, Union
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from ..helpers.Config import get_settings


class OllamaLLM:


    def __init__(self, model: str = None, base_url: str = None, temperature: float = None):
        
        settings = get_settings()
        
        self.model = settings.OLLAMA_MODEL_NAME
        self.base_url = settings.OLLAMA_URL
        self.temperature = settings.TEMPERATURE
        
        self.llm = ChatOllama(
            model=self.model,
            ollama_url=self.base_url,
            temperature=self.temperature,
            reasoning=True
        )

        print(f"Model ready: {self.model}")

    def get_llm(self):
        
        return self.llm

    def _prepare_messages(self, messages: Union[List[Dict[str, str]], List[BaseMessage]]) -> List[BaseMessage]:

        lc_messages = []
        if messages and isinstance(messages[0], BaseMessage):
            return messages  
        # The AI told me to implement this conversion function he says this is a good approach (:
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                lc_messages.append(SystemMessage(content=content))
            elif role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            else:
                raise ValueError(f"Unknown role: {role}")
        
        return lc_messages

    def chat(self, messages: Union[List[Dict[str, str]], List[BaseMessage]]) -> str:
        
        try:
            prepared_messages = self._prepare_messages(messages)
            response = self.llm.invoke(prepared_messages)
            return response.content
        except Exception as e:
            raise Exception(f"Chat failed: {str(e)}")

    def stream(self, messages: Union[List[Dict[str, str]], List[BaseMessage]]):
        
        try:
            prepared_messages = self._prepare_messages(messages)
            for chunk in self.llm.stream(prepared_messages):
                yield chunk.content
        except Exception as e:
            raise Exception(f"Stream failed: {str(e)}")