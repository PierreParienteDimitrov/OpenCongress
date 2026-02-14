"""
Multi-provider chat service with streaming and tool-use support.

Routes chat requests to Anthropic, OpenAI, or Google based on
the user's configured provider and API key. Supports a tool-use
loop: the LLM can call tools to query the database, then stream
a final text response. Each provider also has native web search
enabled so the LLM can look up real-time information.
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
        from anthropic.types import MessageParam, ToolParam

        from services.chat_tools import execute_tool, tools_for_anthropic

        client = Anthropic(api_key=self.api_key)
        db_tools: list[ToolParam] = tools_for_anthropic()  # type: ignore[assignment]

        # Native web search — handled server-side by Claude
        web_search_tool: dict[str, Any] = {
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 3,
        }
        all_tools: list[Any] = [web_search_tool] + db_tools

        conv_messages: list[MessageParam] = [
            {"role": m["role"], "content": m["content"]}  # type: ignore[misc]
            for m in messages
        ]

        for _round in range(MAX_TOOL_ROUNDS + 1):
            is_last_round = _round == MAX_TOOL_ROUNDS

            if is_last_round:
                # Final round: stream text, no tools
                with client.messages.stream(
                    model=self.MODELS["anthropic"],
                    max_tokens=4096,
                    system=system_context,
                    messages=conv_messages,
                ) as stream:
                    for text in stream.text_stream:
                        yield {"type": "text_delta", "content": text}
                break

            # Non-streaming call with tools (includes web search)
            response = client.messages.create(
                model=self.MODELS["anthropic"],
                max_tokens=4096,
                system=system_context,
                messages=conv_messages,
                tools=all_tools,
            )

            has_tool_use = response.stop_reason == "tool_use"

            # Process content blocks
            tool_results: list[dict[str, Any]] = []
            for block in response.content:
                if block.type == "text":
                    if block.text:
                        yield {"type": "text_delta", "content": block.text}
                elif block.type == "tool_use":
                    # Our custom DB tools — execute locally
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
                elif block.type == "server_tool_use":
                    # Server-side web search — emit as a tool call for the UI
                    yield {
                        "type": "tool_call_start",
                        "id": block.id,
                        "name": "web_search",
                        "args": block.input if hasattr(block, "input") else {},
                    }
                elif block.type == "web_search_tool_result":
                    # Web search results from the server — extract source info
                    sources = []
                    if hasattr(block, "content") and block.content:
                        for entry in block.content:
                            if hasattr(entry, "url"):
                                sources.append(
                                    {
                                        "url": entry.url,  # type: ignore[union-attr]
                                        "title": getattr(entry, "title", ""),
                                    }
                                )
                    yield {
                        "type": "tool_call_result",
                        "id": getattr(block, "tool_use_id", ""),
                        "name": "web_search",
                        "result": {"sources": sources},
                    }
                # Skip other block types silently

            if not has_tool_use:
                break

            # Append assistant response and tool results for next round
            conv_messages.append(
                {  # type: ignore[arg-type, misc]
                    "role": "assistant",
                    "content": [b.model_dump() for b in response.content],  # type: ignore[misc]
                }
            )
            if tool_results:
                conv_messages.append(
                    {"role": "user", "content": tool_results}  # type: ignore[arg-type, typeddict-item]
                )

    # ------------------------------------------------------------------
    # OpenAI
    # ------------------------------------------------------------------

    def _stream_openai(
        self, messages: list[dict[str, Any]], system_context: str
    ) -> Generator[ChatEvent, None, None]:
        from openai import OpenAI

        from services.chat_tools import execute_tool, tools_for_openai

        client = OpenAI(api_key=self.api_key)
        db_tools = tools_for_openai()

        # Use Responses API which supports web_search_preview
        all_tools: list[dict[str, Any]] = [
            {"type": "web_search_preview"},
        ] + db_tools

        # Build input: system instructions + conversation
        input_items: list[dict[str, Any]] = []
        if system_context:
            input_items.append({"role": "developer", "content": system_context})
        for m in messages:
            input_items.append({"role": m["role"], "content": m["content"]})

        for _round in range(MAX_TOOL_ROUNDS + 1):
            is_last_round = _round == MAX_TOOL_ROUNDS

            if is_last_round:
                # Final round: stream text, no tools
                stream = client.responses.create(
                    model=self.MODELS["openai"],
                    input=input_items,  # type: ignore[arg-type]
                    stream=True,
                )
                for event in stream:
                    if event.type == "response.output_text.delta":  # type: ignore[union-attr]
                        yield {"type": "text_delta", "content": event.delta}  # type: ignore[union-attr]
                break

            # Non-streaming call with tools
            response = client.responses.create(
                model=self.MODELS["openai"],
                input=input_items,  # type: ignore[arg-type]
                tools=all_tools,  # type: ignore[arg-type]
            )

            has_function_calls = False
            function_results: list[dict[str, Any]] = []

            for item in response.output:
                if item.type == "web_search_call":
                    # Native web search — emit events for the UI
                    yield {
                        "type": "tool_call_start",
                        "id": item.id,
                        "name": "web_search",
                        "args": {},
                    }
                    yield {
                        "type": "tool_call_result",
                        "id": item.id,
                        "name": "web_search",
                        "result": {"status": getattr(item, "status", "completed")},
                    }
                elif item.type == "function_call":
                    has_function_calls = True
                    tool_name = item.name
                    tool_args = json.loads(item.arguments)

                    yield {
                        "type": "tool_call_start",
                        "id": item.call_id,
                        "name": tool_name,
                        "args": tool_args,
                    }

                    result = execute_tool(tool_name, tool_args)

                    yield {
                        "type": "tool_call_result",
                        "id": item.call_id,
                        "name": tool_name,
                        "result": result,
                    }

                    function_results.append(
                        {
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": json.dumps(result),
                        }
                    )
                elif item.type == "message":
                    for content_part in item.content:
                        if content_part.type == "output_text":
                            yield {
                                "type": "text_delta",
                                "content": content_part.text,
                            }
                            # Emit citations as sources
                            annotations = getattr(content_part, "annotations", [])
                            sources = []
                            for ann in annotations:
                                if getattr(ann, "type", "") == "url_citation":
                                    sources.append(
                                        {
                                            "url": ann.url,
                                            "title": getattr(ann, "title", ""),
                                        }
                                    )
                            if sources:
                                yield {
                                    "type": "sources",
                                    "sources": sources,
                                }

            if not has_function_calls:
                break

            # Append response output and function results for next round
            input_items.append({"role": "assistant", "content": response.output})  # type: ignore[dict-item]
            input_items.extend(function_results)

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
        db_tools = tools_for_google()

        # Gemini doesn't allow google_search + function_declarations together,
        # so we use DB tools for intermediate rounds and Google Search for
        # the final streaming round.
        config_with_db_tools = types.GenerateContentConfig(
            max_output_tokens=4096,
            temperature=0.7,
            system_instruction=system_context if system_context else None,
            tools=db_tools,
        )

        config_with_search = types.GenerateContentConfig(
            max_output_tokens=4096,
            temperature=0.7,
            system_instruction=system_context if system_context else None,
            tools=[types.Tool(google_search=types.GoogleSearch())],
        )

        contents: list[types.Content] = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(
                types.Content(role=role, parts=[types.Part(text=msg["content"])])
            )

        for _round in range(MAX_TOOL_ROUNDS + 1):
            is_last_round = _round == MAX_TOOL_ROUNDS

            if is_last_round:
                # Final round: stream with Google Search grounding
                stream_response = client.models.generate_content_stream(
                    model=self.MODELS["google"],
                    contents=contents,
                    config=config_with_search,
                )
                for chunk in stream_response:
                    if chunk.text:
                        yield {"type": "text_delta", "content": chunk.text}
                    # Grounding metadata on streaming chunks
                    candidate = (
                        chunk.candidates[0]
                        if chunk.candidates
                        else None  # type: ignore[index]
                    )
                    if candidate:
                        grounding = getattr(candidate, "grounding_metadata", None)
                        if grounding:
                            yield from self._emit_google_grounding(grounding, _round)
                break

            # Non-streaming call with DB function tools
            sync_response = client.models.generate_content(
                model=self.MODELS["google"],
                contents=contents,
                config=config_with_db_tools,
            )

            has_function_calls = False
            function_responses: list[types.Part] = []

            candidate = sync_response.candidates[0]  # type: ignore[index]

            for part in candidate.content.parts:  # type: ignore[union-attr]
                if part.text:
                    yield {"type": "text_delta", "content": part.text}
                elif part.function_call:
                    has_function_calls = True
                    fc = part.function_call
                    tool_name: str = fc.name  # type: ignore[assignment]
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
            contents.append(candidate.content)  # type: ignore[union-attr, arg-type]
            contents.append(types.Content(role="user", parts=function_responses))

    @staticmethod
    def _emit_google_grounding(
        grounding: Any, round_idx: int
    ) -> Generator[ChatEvent, None, None]:
        """Extract grounding metadata from Google Search and yield events."""
        sources = []
        chunks = getattr(grounding, "grounding_chunks", None) or []
        for gc in chunks:
            web = getattr(gc, "web", None)
            if web:
                sources.append(
                    {
                        "url": getattr(web, "uri", ""),
                        "title": getattr(web, "title", ""),
                    }
                )
        if sources:
            yield {
                "type": "tool_call_start",
                "id": f"google_search_{round_idx}",
                "name": "web_search",
                "args": {"queries": getattr(grounding, "web_search_queries", [])},
            }
            yield {
                "type": "tool_call_result",
                "id": f"google_search_{round_idx}",
                "name": "web_search",
                "result": {"sources": sources},
            }
