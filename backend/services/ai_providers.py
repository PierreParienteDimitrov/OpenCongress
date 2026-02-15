"""
AI provider backends.

Each provider implements two methods:
    generate(prompt, max_tokens, temperature) -> (text, token_count)
    generate_with_web_search(prompt, max_tokens, temperature) -> (text, token_count)
"""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseProvider(ABC):
    """Interface that every AI provider must implement."""

    MODEL: str

    @abstractmethod
    def generate(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> tuple[str, int]: ...

    @abstractmethod
    def generate_with_web_search(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> tuple[str, int]: ...


# ── Anthropic ────────────────────────────────────────────────────────────


class AnthropicProvider(BaseProvider):
    MODEL = "claude-sonnet-4-5-20250929"

    def __init__(self, api_key: str):
        import anthropic

        self.client = anthropic.Anthropic(api_key=api_key, timeout=60.0)

    def generate(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> tuple[str, int]:
        response = self.client.messages.create(
            model=self.MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        block = response.content[0]
        text = block.text.strip() if hasattr(block, "text") else ""
        tokens = response.usage.input_tokens + response.usage.output_tokens
        return text, tokens

    def generate_with_web_search(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> tuple[str, int]:
        response = self.client.messages.create(
            model=self.MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
        )
        text_parts = [
            block.text for block in response.content if hasattr(block, "text")
        ]
        text = "\n".join(text_parts).strip()
        tokens = response.usage.input_tokens + response.usage.output_tokens
        return text, tokens


# ── Google Gemini ────────────────────────────────────────────────────────


class GeminiProvider(BaseProvider):
    MODEL = "gemini-2.5-flash"

    def __init__(self, api_key: str):
        from google import genai
        from google.genai import types

        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=60),
        )

    def generate(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> tuple[str, int]:
        from google.genai import types

        response = self.client.models.generate_content(
            model=self.MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        assert response.text is not None
        assert response.usage_metadata is not None
        text = response.text.strip()
        tokens: int = response.usage_metadata.total_token_count  # type: ignore[assignment]
        return text, tokens

    def generate_with_web_search(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> tuple[str, int]:
        from google.genai import types

        response = self.client.models.generate_content(
            model=self.MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )
        assert response.text is not None
        assert response.usage_metadata is not None
        text = response.text.strip()
        tokens: int = response.usage_metadata.total_token_count  # type: ignore[assignment]
        return text, tokens


# ── OpenAI ───────────────────────────────────────────────────────────────


class OpenAIProvider(BaseProvider):
    MODEL = "gpt-4o"

    def __init__(self, api_key: str):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key, timeout=60.0)

    def generate(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> tuple[str, int]:
        response = self.client.chat.completions.create(
            model=self.MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.choices[0].message.content
        text = content.strip() if content else ""
        assert response.usage is not None
        tokens = response.usage.prompt_tokens + response.usage.completion_tokens
        return text, tokens

    def generate_with_web_search(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> tuple[str, int]:
        response = self.client.responses.create(
            model=self.MODEL,
            tools=[{"type": "web_search_preview"}],  # type: ignore[list-item]
            input=prompt,
        )
        text = response.output_text.strip()
        assert response.usage is not None
        tokens = response.usage.input_tokens + response.usage.output_tokens
        return text, tokens


# ── Factory ──────────────────────────────────────────────────────────────

PROVIDERS: dict[str, type[BaseProvider]] = {
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
}
