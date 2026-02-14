"use client";

import type { ChatModelAdapter, ChatModelRunResult } from "@assistant-ui/react";
import { getSession } from "next-auth/react";
import type { PageContext } from "@/lib/chat-context";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface ToolCallState {
  toolCallId: string;
  toolName: string;
  args: Record<string, unknown>;
  argsText: string;
  result: unknown | undefined;
}

interface Source {
  url: string;
  title: string;
}

export function createDjangoChatAdapter(
  provider: string,
  pageContext: PageContext | null,
): ChatModelAdapter {
  return {
    async *run({ messages, abortSignal }) {
      const session = await getSession();
      if (!session?.djangoAccessToken) {
        throw new Error("Not authenticated");
      }

      // Convert assistant-ui message format to our Django API format
      const apiMessages = messages.map((m) => ({
        role: m.role,
        content: m.content
          .filter((c) => c.type === "text")
          .map((c) => {
            if (c.type === "text") return c.text;
            return "";
          })
          .join("\n"),
      }));

      const response = await fetch(`${API_BASE_URL}/auth/chat/stream/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.djangoAccessToken}`,
        },
        body: JSON.stringify({
          provider,
          messages: apiMessages,
          page_context: pageContext || { type: "home", data: {} },
        }),
        signal: abortSignal,
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `API error: ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error("No response body");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullText = "";
      const toolCalls = new Map<string, ToolCallState>();
      const sources: Source[] = [];
      // Buffer for incomplete SSE lines split across chunks
      let lineBuffer = "";

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          lineBuffer += decoder.decode(value, { stream: true });
          const lines = lineBuffer.split("\n");
          // Keep the last (possibly incomplete) line in the buffer
          lineBuffer = lines.pop() ?? "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            let data: Record<string, unknown>;
            try {
              data = JSON.parse(line.slice(6));
            } catch {
              continue; // Ignore malformed SSE lines
            }

            if (data.chunk) {
              fullText += data.chunk as string;
            } else if (data.tool_call) {
              const tc = data.tool_call as {
                id: string;
                name: string;
                args: Record<string, unknown>;
              };
              toolCalls.set(tc.id, {
                toolCallId: tc.id,
                toolName: tc.name,
                args: tc.args,
                argsText: JSON.stringify(tc.args, null, 2),
                result: undefined,
              });
            } else if (data.tool_result) {
              const tr = data.tool_result as {
                id: string;
                name: string;
                result: unknown;
              };
              const existing = toolCalls.get(tr.id);
              if (existing) {
                existing.result = tr.result;
              }
            } else if (data.sources) {
              // Collect web search citation sources
              const newSources = data.sources as Source[];
              for (const s of newSources) {
                if (!sources.some((x) => x.url === s.url)) {
                  sources.push(s);
                }
              }
            } else if (data.error) {
              const raw = data.error as string;
              // Show a friendly message for known provider errors
              if (
                raw.includes("INVALID_ARGUMENT") ||
                raw.includes("function calling")
              ) {
                throw new Error(
                  "This feature is not supported by your API plan. Please try a different model or upgrade your API key.",
                );
              }
              throw new Error(raw);
            } else if (data.done) {
              // Stream complete — append sources as markdown links
              if (sources.length > 0) {
                fullText +=
                  "\n\n---\n**Sources:**\n" +
                  sources
                    .map((s) => `- [${s.title || s.url}](${s.url})`)
                    .join("\n");
              }
            }

            // Build content array with text + tool-call parts
            const content: ChatModelRunResult["content"] = [];

            if (fullText) {
              (content as unknown[]).push({
                type: "text" as const,
                text: fullText,
              });
            }

            for (const tc of toolCalls.values()) {
              (content as unknown[]).push({
                type: "tool-call" as const,
                toolCallId: tc.toolCallId,
                toolName: tc.toolName,
                args: tc.args,
                argsText: tc.argsText,
                ...(tc.result !== undefined ? { result: tc.result } : {}),
              });
            }

            if (content && content.length > 0) {
              yield { content } satisfies ChatModelRunResult;
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    },
  };
}
