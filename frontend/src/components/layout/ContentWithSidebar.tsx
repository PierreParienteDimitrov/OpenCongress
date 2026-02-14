"use client";

import { Suspense, type ReactNode } from "react";
import { useChatUI } from "@/lib/chat-store";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { cn } from "@/lib/utils";

const SIDEBAR_WIDTH = 400;

export function ContentWithSidebar({ children }: { children: ReactNode }) {
  const isOpen = useChatUI((s) => s.isOpen);
  const isExpanded = useChatUI((s) => s.isExpanded);

  const showSidebar = isOpen && isExpanded;

  return (
    <>
      <div className="flex flex-1">
        <div
          className={cn(
            "flex-1 min-w-0",
            showSidebar && "transition-all duration-300",
          )}
        >
          {children}
        </div>

        {/* Sidebar slot — ChatInterface portals into this when expanded */}
        <div
          id="chat-sidebar-slot"
          className="shrink-0 sticky top-[var(--navbar-height)] border-l border-border bg-background overflow-hidden transition-[width] duration-300 h-[calc(100vh-var(--navbar-height))]"
          style={{ width: showSidebar ? SIDEBAR_WIDTH : 0 }}
        />
      </div>

      <Suspense>
        <ChatInterface />
      </Suspense>
    </>
  );
}
