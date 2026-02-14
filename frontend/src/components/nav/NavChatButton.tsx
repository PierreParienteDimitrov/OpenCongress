"use client";

import { useChatUI } from "@/lib/chat-store";

export function NavChatButton() {
  const toggle = useChatUI((s) => s.toggle);

  return (
    <button
      onClick={toggle}
      className="relative hidden lg:inline-flex items-center border border-transparent mr-2 cursor-pointer overflow-hidden"
      style={{
        borderImage: "linear-gradient(to right, #ef4444, #3b82f6) 1",
      }}
    >
      {/* Zoomed-in star from the flag — faint background motif */}
      <svg
        className="pointer-events-none absolute -right-3 -top-3 size-14"
        viewBox="0 0 100 100"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id="star-grad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#ef4444" stopOpacity="0.18" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.18" />
          </linearGradient>
        </defs>
        <polygon
          points="50,0 61,35 98,35 68,57 79,91 50,70 21,91 32,57 2,35 39,35"
          fill="url(#star-grad)"
        />
      </svg>
      <span className="relative flex items-center px-6 py-1.5 text-sm font-medium text-nav-foreground">
        Ask AI
      </span>
    </button>
  );
}
