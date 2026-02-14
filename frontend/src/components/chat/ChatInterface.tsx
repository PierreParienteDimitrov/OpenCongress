"use client";

import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import { useSession } from "next-auth/react";
import { useQuery } from "@tanstack/react-query";
import {
  MessageSquare,
  Send,
  Settings,
  Loader2,
} from "lucide-react";
import Link from "next/link";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { fetchAPIKeys, streamChat, type ConfiguredAPIKey } from "@/lib/api-client";
import { useChatContext } from "@/lib/chat-context";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export function ChatInterface() {
  const { data: session } = useSession();
  const pageContext = useChatContext();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [selectedProviderOverride, setSelectedProvider] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { data: apiKeys = [] } = useQuery<ConfiguredAPIKey[]>({
    queryKey: ["api-keys"],
    queryFn: fetchAPIKeys,
    enabled: !!session,
  });

  // Derive selected provider: use override if set and still valid, else first available
  const selectedProvider = useMemo(() => {
    if (selectedProviderOverride && apiKeys.some((k) => k.provider === selectedProviderOverride)) {
      return selectedProviderOverride;
    }
    return apiKeys.length > 0 ? apiKeys[0].provider : null;
  }, [apiKeys, selectedProviderOverride]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(scrollToBottom, [messages, scrollToBottom]);

  // Focus input when sheet opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || !selectedProvider || isStreaming) return;

    const userMessage: Message = { role: "user", content: trimmed };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput("");
    setIsStreaming(true);

    // Add empty assistant message to be filled by stream
    let assistantContent = "";
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    try {
      await streamChat({
        provider: selectedProvider,
        messages: newMessages,
        pageContext: pageContext || { type: "home", data: {} },
        onChunk: (chunk) => {
          assistantContent += chunk;
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              role: "assistant",
              content: assistantContent,
            };
            return updated;
          });
        },
        onDone: () => {
          setIsStreaming(false);
        },
        onError: (error) => {
          assistantContent += assistantContent
            ? `\n\n[Error: ${error}]`
            : `Error: ${error}`;
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              role: "assistant",
              content: assistantContent,
            };
            return updated;
          });
          setIsStreaming(false);
        },
      });
    } catch {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: "An unexpected error occurred. Please try again.",
        };
        return updated;
      });
      setIsStreaming(false);
    }
  };

  // Don't render at all when not logged in
  if (!session) return null;

  const hasKeys = apiKeys.length > 0;

  return (
    <>
      {/* Floating trigger button */}
      <Sheet open={isOpen} onOpenChange={setIsOpen}>
        <SheetTrigger asChild>
          <Button
            className="fixed bottom-6 right-6 z-50 size-14 rounded-full shadow-lg"
            size="icon"
          >
            <MessageSquare className="size-6" />
          </Button>
        </SheetTrigger>

        <SheetContent
          side="right"
          className="flex w-full flex-col p-0 sm:max-w-md"
        >
          {/* Header */}
          <SheetHeader className="border-b px-4 py-3">
            <div className="flex items-center justify-between">
              <SheetTitle className="text-base">AI Assistant</SheetTitle>
              {messages.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setMessages([])}
                  className="text-xs text-muted-foreground"
                >
                  Clear chat
                </Button>
              )}
            </div>
            {hasKeys && (
              <div className="flex gap-1.5 pt-1">
                {apiKeys.map((key) => (
                  <Badge
                    key={key.provider}
                    variant={
                      selectedProvider === key.provider
                        ? "default"
                        : "outline"
                    }
                    className="cursor-pointer text-xs"
                    onClick={() => setSelectedProvider(key.provider)}
                  >
                    {key.provider_display}
                  </Badge>
                ))}
              </div>
            )}
          </SheetHeader>

          {/* Body */}
          {!hasKeys ? (
            <div className="flex flex-1 items-center justify-center p-6">
              <div className="text-center space-y-3">
                <Settings className="mx-auto size-10 text-muted-foreground/40" />
                <div>
                  <p className="font-medium text-sm">
                    No API keys configured
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Add at least one AI provider API key in settings to
                    use the chat.
                  </p>
                </div>
                <Button asChild size="sm" variant="outline">
                  <Link href="/settings" onClick={() => setIsOpen(false)}>
                    Go to Settings
                  </Link>
                </Button>
              </div>
            </div>
          ) : (
            <>
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {messages.length === 0 && (
                  <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
                    <MessageSquare className="size-8 mb-2 opacity-30" />
                    <p className="text-sm">
                      Ask me anything about{" "}
                      {pageContext?.type === "bill"
                        ? "this bill"
                        : pageContext?.type === "vote"
                          ? "this vote"
                          : pageContext?.type === "member"
                            ? "this member"
                            : "congressional activity"}
                      .
                    </p>
                  </div>
                )}

                {messages.map((msg, i) => (
                  <div
                    key={i}
                    className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                        msg.role === "user"
                          ? "bg-primary text-primary-foreground"
                          : "bg-secondary text-secondary-foreground"
                      }`}
                    >
                      <p className="whitespace-pre-wrap break-words">
                        {msg.content}
                        {isStreaming &&
                          i === messages.length - 1 &&
                          msg.role === "assistant" && (
                            <span className="inline-block ml-1 w-1.5 h-4 bg-current animate-pulse" />
                          )}
                      </p>
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="border-t p-3">
                <div className="flex gap-2">
                  <input
                    ref={inputRef}
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleSend();
                      }
                    }}
                    placeholder="Type your message..."
                    disabled={isStreaming}
                    className="flex-1 rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
                  />
                  <Button
                    onClick={handleSend}
                    disabled={isStreaming || !input.trim()}
                    size="icon"
                    className="shrink-0"
                  >
                    {isStreaming ? (
                      <Loader2 className="size-4 animate-spin" />
                    ) : (
                      <Send className="size-4" />
                    )}
                  </Button>
                </div>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </>
  );
}
