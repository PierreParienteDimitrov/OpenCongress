"use client";

import { useState } from "react";
import { Search } from "lucide-react";
import { CommandPalette } from "@/components/search/CommandPalette";

export function NavSearchButton() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="inline-flex items-center gap-2 mr-2 bg-nav-foreground/10 px-3 py-1.5 text-nav-foreground/60 hover:text-nav-foreground hover:bg-nav-foreground/15 transition-colors cursor-pointer"
      >
        <Search className="size-3.5" />
        <kbd className="pointer-events-none hidden sm:inline-flex items-center gap-0.5 text-[11px] font-mono">
          <span className="text-sm">⌘</span>K
        </kbd>
        <span className="sr-only">Search</span>
      </button>
      <CommandPalette open={open} onOpenChange={setOpen} />
    </>
  );
}
