"use client";

import { useChatUI } from "@/lib/chat-store";

export function NavChatButton() {
  const toggle = useChatUI((s) => s.toggle);

  return (
    <button
      onClick={toggle}
      className="hidden lg:inline-flex items-center rounded-md p-px cursor-pointer bg-gradient-to-r from-glory-blue-400 to-glory-red-400 hover:from-glory-blue-300 hover:to-glory-red-300 transition-all"
    >
      <span className="flex items-center rounded-[5px] bg-nav px-3 py-1.5 text-sm font-medium text-nav-foreground">
        AI Bot
      </span>
    </button>
  );
}
