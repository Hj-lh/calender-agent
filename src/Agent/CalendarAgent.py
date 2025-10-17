from typing import List, Dict, Optional
from datetime import datetime
import pytz
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import HumanMessage, AIMessage
from ..helpers.Config import get_settings
from ..LLMProvider.OllamaProvider import OllamaLLM
from .tools import get_calendar_tools
from .prompts import CALENDAR_AGENT_PROMPT


class CalendarAgent:
    def __init__(self, llm: Optional[OllamaLLM] = None, calendar_provider=None, verbose: bool = True, timezone: str = None):
        self.llm = llm if llm else OllamaLLM()

        self.tools = get_calendar_tools(calendar_provider)
        print(f"\nLoaded {len(self.tools)} tools:")
        for tool in self.tools:
            print(f"   - {tool.name}")
        print()
        llm_with_tools = self.llm.get_llm().bind_tools(self.tools)

        self.agent = create_tool_calling_agent(
            llm=llm_with_tools,
            tools=self.tools,
            prompt=CALENDAR_AGENT_PROMPT,
        )

        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=verbose,
            handle_parsing_errors=True,
            max_iterations=5,
            return_intermediate_steps=False
        )

        self.chat_history: List = []
        print(f"Calendar Agent started. {self.llm.model}")

    def chat(self, user_message: str) -> str:

        try:
            settings = get_settings()
            user_tz = pytz.timezone(settings.TIMEZONE)
            current_time = datetime.now(user_tz)
            context_message = (
                f"Current date and time: {current_time.strftime('%A, %B %d, %Y at %I:%M %p')}\n\n"
                f"User's timezone: {settings.TIMEZONE}\n\n"
                f"User request: {user_message}"
            )

            result = self.agent_executor.invoke({
                "input": context_message,
                "chat_history": self.chat_history
            })
            self.chat_history.append(HumanMessage(content=user_message))
            self.chat_history.append(AIMessage(content=result['output']))

            return result['output']
        except Exception as e:
            return f"❌ An error occurred while processing your request: {str(e)}"
        
    def clear_history(self):
        self.chat_history = []
        print("Chat history cleared.")

    def get_history(self) -> List[Dict[str, str]]:
        history = []
        for msg in self.chat_history:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history.append({"role": "assistant", "content": msg.content})
        return history