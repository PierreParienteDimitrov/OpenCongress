"use client";

import { Suspense, type ReactNode } from "react";
import { useChatUI } from "@/lib/chat-store";
import { ChatInterface } from "@/components/chat/ChatInterface";

const SIDEBAR_WIDTH = 400;

export function ContentWithSidebar({
  navbar,
  children,
}: {
  navbar: ReactNode;
  children: ReactNode;
}) {
  const isOpen = useChatUI((s) => s.isOpen);
  const isExpanded = useChatUI((s) => s.isExpanded);

  const showSidebar = isOpen && isExpanded;

  return (
    <>
      <div
        className="flex min-h-screen flex-col transition-[margin] duration-300"
        style={{ marginRight: showSidebar ? SIDEBAR_WIDTH : 0 }}
      >
        {navbar}
        <div className="bg-amber-500/15 border-b border-amber-500/30 px-4 py-1.5 text-center text-sm text-amber-400">
          Alpha version — Under active development. Expect bugs and frequent
          changes.
        </div>
        <div className="flex-1 min-w-0">{children}</div>
      </div>

      {/* Sidebar slot — fixed full-height panel on right, overlaps navbar */}
      <div
        id="chat-sidebar-slot"
        className="fixed top-0 right-0 z-50 h-screen border-l border-border bg-background overflow-hidden transition-[width] duration-300"
        style={{ width: showSidebar ? SIDEBAR_WIDTH : 0 }}
      />

      <Suspense>
        <ChatInterface />
      </Suspense>
    </>
  );
}
