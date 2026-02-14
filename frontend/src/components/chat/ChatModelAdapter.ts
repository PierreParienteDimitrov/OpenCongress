"use client";

import type { ChatModelAdapter } from "@assistant-ui/react";
import { getSession } from "next-auth/react";
import type { PageContext } from "@/lib/chat-context";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

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

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const text = decoder.decode(value);
          const lines = text.split("\n");

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
              yield {
                content: [{ type: "text" as const, text: fullText }],
              };
            } else if (data.error) {
              throw new Error(data.error as string);
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    },
  };
}
