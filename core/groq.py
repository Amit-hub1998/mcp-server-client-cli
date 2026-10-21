from typing import Optional

from groq import Groq
from groq.types.chat import ChatCompletion, ChatCompletionMessage


class GroqService:
    def __init__(self, model: str, api_key: str):
        self.client = Groq(api_key=api_key)
        self.model = model

    def add_user_message(self, messages: list[dict], message):
        messages.append({"role": "user", "content": message})

    def add_assistant_message(
        self, messages: list[dict], message: ChatCompletionMessage
    ):
        messages.append(message.model_dump(exclude_none=True))

    def text_from_message(self, message: ChatCompletionMessage) -> str:
        return message.content or ""

    def chat(
        self,
        messages: list[dict],
        system=None,
        temperature=1.0,
        stop_sequences: Optional[list[str]] = None,
        tools=None,
    ) -> ChatCompletion:
        chat_messages = messages
        if system:
            chat_messages = [{"role": "system", "content": system}, *messages]

        params = {
            "model": self.model,
            "max_tokens": 8000,
            "messages": chat_messages,
            "temperature": temperature,
            "stop": stop_sequences or None,
        }

        if tools:
            params["tools"] = tools

        return self.client.chat.completions.create(**params)
