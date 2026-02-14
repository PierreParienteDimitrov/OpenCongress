"""
Multi-provider chat service with streaming support.

Routes chat requests to Anthropic, OpenAI, or Google based on
the user's configured provider and API key.
"""

import logging
from typing import Generator

logger = logging.getLogger(__name__)


class ChatService:
    """Unified streaming chat interface for multiple AI providers."""

    # Default models per provider
    MODELS = {
        "anthropic": "claude-sonnet-4-5-20250929",
        "openai": "gpt-4o",
        "google": "gemini-2.0-flash",
    }

    def __init__(self, provider: str, api_key: str):
        if provider not in self.MODELS:
            raise ValueError(f"Unknown provider: {provider}")
        self.provider = provider
        self.api_key = api_key

    def stream_chat(
        self,
        messages: list[dict],
        system_context: str = "",
    ) -> Generator[str, None, None]:
        """
        Stream chat response chunks.

        Args:
            messages: List of {"role": "user"|"assistant", "content": "..."}
            system_context: System prompt with page context.

        Yields:
            Text chunks as they arrive from the provider.
        """
        if self.provider == "anthropic":
            yield from self._stream_anthropic(messages, system_context)
        elif self.provider == "openai":
            yield from self._stream_openai(messages, system_context)
        elif self.provider == "google":
            yield from self._stream_google(messages, system_context)

    def _stream_anthropic(
        self, messages: list[dict], system_context: str
    ) -> Generator[str, None, None]:
        from anthropic import Anthropic

        client = Anthropic(api_key=self.api_key)
        with client.messages.stream(
            model=self.MODELS["anthropic"],
            max_tokens=2048,
            system=system_context,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text

    def _stream_openai(
        self, messages: list[dict], system_context: str
    ) -> Generator[str, None, None]:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)

        openai_messages = []
        if system_context:
            openai_messages.append({"role": "system", "content": system_context})
        openai_messages.extend(messages)

        stream = client.chat.completions.create(
            model=self.MODELS["openai"],
            messages=openai_messages,
            max_tokens=2048,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    def _stream_google(
        self, messages: list[dict], system_context: str
    ) -> Generator[str, None, None]:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.api_key)

        # Convert messages to Gemini content format
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(
                types.Content(role=role, parts=[types.Part(text=msg["content"])])
            )

        config = types.GenerateContentConfig(
            max_output_tokens=2048,
            temperature=0.7,
            system_instruction=system_context if system_context else None,
        )

        response = client.models.generate_content_stream(
            model=self.MODELS["google"],
            contents=contents,
            config=config,
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text
