"""
Multi-provider chat service with streaming and tool-use support.

Routes chat requests to Anthropic, OpenAI, or Google based on
the user's configured provider and API key. Supports a tool-use
loop: the LLM can call tools to query the database, then stream
a final text response.
"""

import json
import logging
from typing import Any, Generator

logger = logging.getLogger(__name__)

# Maximum rounds of tool calls before forcing a text response
MAX_TOOL_ROUNDS = 3

# Type alias for events yielded by the stream
ChatEvent = dict[str, Any]


class ChatService:
    """Unified streaming chat interface for multiple AI providers."""

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
        messages: list[dict[str, Any]],
        system_context: str = "",
    ) -> Generator[ChatEvent, None, None]:
        """
        Stream chat events including text deltas and tool calls.

        Yields dicts with a "type" key:
          - {"type": "text_delta", "content": "..."}
          - {"type": "tool_call_start", "id": "...", "name": "...", "args": {...}}
          - {"type": "tool_call_result", "id": "...", "name": "...", "result": {...}}
        """
        if self.provider == "anthropic":
            yield from self._stream_anthropic(messages, system_context)
        elif self.provider == "openai":
            yield from self._stream_openai(messages, system_context)
        elif self.provider == "google":
            yield from self._stream_google(messages, system_context)

    # ------------------------------------------------------------------
    # Anthropic
    # ------------------------------------------------------------------

    def _stream_anthropic(
        self, messages: list[dict[str, Any]], system_context: str
    ) -> Generator[ChatEvent, None, None]:
        from anthropic import Anthropic

        from services.chat_tools import execute_tool, tools_for_anthropic

        client = Anthropic(api_key=self.api_key)
        tools = tools_for_anthropic()
        conv_messages: list[dict[str, Any]] = [
            {"role": m["role"], "content": m["content"]} for m in messages
        ]

        for _round in range(MAX_TOOL_ROUNDS + 1):
            is_last_round = _round == MAX_TOOL_ROUNDS

            if is_last_round:
                # Final round: stream text, no tools
                with client.messages.stream(
                    model=self.MODELS["anthropic"],
                    max_tokens=2048,
                    system=system_context,
                    messages=conv_messages,
                ) as stream:
                    for text in stream.text_stream:
                        yield {"type": "text_delta", "content": text}
                break

            # Non-streaming call with tools
            response = client.messages.create(
                model=self.MODELS["anthropic"],
                max_tokens=2048,
                system=system_context,
                messages=conv_messages,
                tools=tools,
            )

            has_tool_use = response.stop_reason == "tool_use"

            # Process content blocks
            tool_results: list[dict[str, Any]] = []
            for block in response.content:
                if block.type == "text" and block.text:
                    yield {"type": "text_delta", "content": block.text}
                elif block.type == "tool_use":
                    yield {
                        "type": "tool_call_start",
                        "id": block.id,
                        "name": block.name,
                        "args": block.input,
                    }
                    result = execute_tool(block.name, block.input)
                    yield {
                        "type": "tool_call_result",
                        "id": block.id,
                        "name": block.name,
                        "result": result,
                    }
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        }
                    )

            if not has_tool_use:
                break

            # Append assistant response and tool results for next round
            conv_messages.append(
                {
                    "role": "assistant",
                    "content": [b.model_dump() for b in response.content],
                }
            )
            conv_messages.append({"role": "user", "content": tool_results})

    # ------------------------------------------------------------------
    # OpenAI
    # ------------------------------------------------------------------

    def _stream_openai(
        self, messages: list[dict[str, Any]], system_context: str
    ) -> Generator[ChatEvent, None, None]:
        from openai import OpenAI

        from services.chat_tools import execute_tool, tools_for_openai

        client = OpenAI(api_key=self.api_key)
        tools = tools_for_openai()

        openai_messages: list[dict[str, Any]] = []
        if system_context:
            openai_messages.append({"role": "system", "content": system_context})
        for m in messages:
            openai_messages.append({"role": m["role"], "content": m["content"]})

        for _round in range(MAX_TOOL_ROUNDS + 1):
            is_last_round = _round == MAX_TOOL_ROUNDS

            if is_last_round:
                # Final round: stream text, no tools
                stream = client.chat.completions.create(
                    model=self.MODELS["openai"],
                    messages=openai_messages,
                    max_tokens=2048,
                    stream=True,
                )
                for chunk in stream:
                    if not hasattr(chunk, "choices") or not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield {"type": "text_delta", "content": delta.content}
                break

            # Non-streaming call with tools
            response = client.chat.completions.create(
                model=self.MODELS["openai"],
                messages=openai_messages,
                max_tokens=2048,
                tools=tools,
            )

            choice = response.choices[0]
            message = choice.message

            if message.content:
                yield {"type": "text_delta", "content": message.content}

            if not message.tool_calls:
                break

            # Append assistant message with tool calls
            openai_messages.append(message.model_dump())

            for tc in message.tool_calls:
                tool_name = tc.function.name
                tool_args = json.loads(tc.function.arguments)

                yield {
                    "type": "tool_call_start",
                    "id": tc.id,
                    "name": tool_name,
                    "args": tool_args,
                }

                result = execute_tool(tool_name, tool_args)

                yield {
                    "type": "tool_call_result",
                    "id": tc.id,
                    "name": tool_name,
                    "result": result,
                }

                openai_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result),
                    }
                )

    # ------------------------------------------------------------------
    # Google GenAI
    # ------------------------------------------------------------------

    def _stream_google(
        self, messages: list[dict[str, Any]], system_context: str
    ) -> Generator[ChatEvent, None, None]:
        from google import genai
        from google.genai import types

        from services.chat_tools import execute_tool, tools_for_google

        client = genai.Client(api_key=self.api_key)
        tools = tools_for_google()

        contents: list[types.Content] = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(
                types.Content(role=role, parts=[types.Part(text=msg["content"])])
            )

        config = types.GenerateContentConfig(
            max_output_tokens=2048,
            temperature=0.7,
            system_instruction=system_context if system_context else None,
            tools=tools,
        )

        config_no_tools = types.GenerateContentConfig(
            max_output_tokens=2048,
            temperature=0.7,
            system_instruction=system_context if system_context else None,
        )

        for _round in range(MAX_TOOL_ROUNDS + 1):
            is_last_round = _round == MAX_TOOL_ROUNDS

            if is_last_round:
                # Final round: stream text, no tools
                response = client.models.generate_content_stream(
                    model=self.MODELS["google"],
                    contents=contents,
                    config=config_no_tools,
                )
                for chunk in response:
                    if chunk.text:
                        yield {"type": "text_delta", "content": chunk.text}
                break

            # Non-streaming call with tools
            response = client.models.generate_content(
                model=self.MODELS["google"],
                contents=contents,
                config=config,
            )

            has_function_calls = False
            function_responses: list[types.Part] = []

            for part in response.candidates[0].content.parts:
                if part.text:
                    yield {"type": "text_delta", "content": part.text}
                elif part.function_call:
                    has_function_calls = True
                    fc = part.function_call
                    tool_name = fc.name
                    tool_args = dict(fc.args) if fc.args else {}

                    call_id = f"google_{tool_name}_{_round}"
                    yield {
                        "type": "tool_call_start",
                        "id": call_id,
                        "name": tool_name,
                        "args": tool_args,
                    }

                    result = execute_tool(tool_name, tool_args)

                    yield {
                        "type": "tool_call_result",
                        "id": call_id,
                        "name": tool_name,
                        "result": result,
                    }

                    function_responses.append(
                        types.Part(
                            function_response=types.FunctionResponse(
                                name=tool_name,
                                response=result,
                            )
                        )
                    )

            if not has_function_calls:
                break

            # Append model response and tool results for next round
            contents.append(response.candidates[0].content)
            contents.append(types.Content(role="user", parts=function_responses))
