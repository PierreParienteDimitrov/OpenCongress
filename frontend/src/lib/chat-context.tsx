"use client";

import { createContext, useContext, type ReactNode } from "react";

export interface PageContext {
  type:
    | "bill"
    | "vote"
    | "member"
    | "chamber"
    | "calendar"
    | "this-week"
    | "home";
  data: Record<string, unknown>;
}

const ChatContext = createContext<PageContext | null>(null);

export function ChatContextProvider({
  children,
  context,
}: {
  children: ReactNode;
  context: PageContext;
}) {
  return (
    <ChatContext.Provider value={context}>{children}</ChatContext.Provider>
  );
}

export function useChatContext(): PageContext | null {
  return useContext(ChatContext);
}
