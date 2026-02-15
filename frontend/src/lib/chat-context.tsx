"use client";

import { useEffect, type ReactNode } from "react";
import { useChatUI } from "./chat-store";

export interface PageContext {
  type:
    | "bill"
    | "vote"
    | "member"
    | "chamber"
    | "committee"
    | "calendar"
    | "this-week"
    | "home";
  data: Record<string, unknown>;
}

const DEFAULT_CONTEXT: PageContext = { type: "home", data: {} };

/**
 * Sets the page context in the global Zustand store when mounted.
 * Resets to "home" on unmount so context doesn't go stale on pages
 * without a provider (e.g. /settings, /login).
 */
export function ChatContextProvider({
  children,
  context,
}: {
  children: ReactNode;
  context: PageContext;
}) {
  const setPageContext = useChatUI((s) => s.setPageContext);
  const serialized = JSON.stringify(context);

  useEffect(() => {
    setPageContext(JSON.parse(serialized));
    return () => {
      setPageContext(DEFAULT_CONTEXT);
    };
  }, [serialized, setPageContext]);

  return <>{children}</>;
}

export function useChatContext(): PageContext {
  return useChatUI((s) => s.pageContext);
}
