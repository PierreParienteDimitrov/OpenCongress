"use client";

import { Suspense, useCallback, useRef, useState, type ReactNode } from "react";
import { useChatUI } from "@/lib/chat-store";
import { ChatInterface } from "@/components/chat/ChatInterface";

export function ContentWithSidebar({
  navbar,
  children,
}: {
  navbar: ReactNode;
  children: ReactNode;
}) {
  const isOpen = useChatUI((s) => s.isOpen);
  const isExpanded = useChatUI((s) => s.isExpanded);
  const sidebarWidth = useChatUI((s) => s.sidebarWidth);
  const setSidebarWidth = useChatUI((s) => s.setSidebarWidth);

  const showSidebar = isOpen && isExpanded;
  const isResizing = useRef(false);
  const [isDragging, setIsDragging] = useState(false);

  const startResize = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      isResizing.current = true;
      setIsDragging(true);

      document.body.classList.add("select-none");
      document.body.style.cursor = "col-resize";

      const onMouseMove = (ev: MouseEvent) => {
        const newWidth = window.innerWidth - ev.clientX;
        setSidebarWidth(newWidth);
      };

      const onMouseUp = () => {
        isResizing.current = false;
        setIsDragging(false);
        document.body.classList.remove("select-none");
        document.body.style.cursor = "";
        document.removeEventListener("mousemove", onMouseMove);
        document.removeEventListener("mouseup", onMouseUp);
      };

      document.addEventListener("mousemove", onMouseMove);
      document.addEventListener("mouseup", onMouseUp);
    },
    [setSidebarWidth],
  );

  const transitionClass = isDragging ? "" : "transition-[margin] duration-300";
  const slotTransitionClass = isDragging
    ? ""
    : "transition-[width] duration-300";

  return (
    <>
      <div
        className={`flex min-h-screen flex-col ${transitionClass}`}
        style={{ marginRight: showSidebar ? sidebarWidth : 0 }}
      >
        {navbar}
        <div className="bg-amber-500/15 border-b border-amber-500/30 px-4 py-1.5 text-center text-sm text-amber-400">
          Alpha version — Under active development. Data is continuously
          refined and improved. All information should be independently
          verified.
        </div>
        <div className="flex-1 min-w-0">{children}</div>
      </div>

      {/* Sidebar slot — fixed full-height panel on right, overlaps navbar */}
      <div
        id="chat-sidebar-slot"
        className={`fixed top-0 right-0 z-50 h-screen border-l border-border bg-background overflow-hidden ${slotTransitionClass}`}
        style={{ width: showSidebar ? sidebarWidth : 0 }}
      >
        {/* Resize drag handle on the left edge */}
        {showSidebar && (
          <div
            onMouseDown={startResize}
            className="absolute top-0 left-0 z-10 h-full w-1 cursor-col-resize hover:bg-primary/20 active:bg-primary/30 transition-colors"
          />
        )}
      </div>

      <Suspense>
        <ChatInterface />
      </Suspense>
    </>
  );
}
