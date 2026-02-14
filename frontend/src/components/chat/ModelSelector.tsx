"use client";

import { ChevronDown } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import { type AIProvider, useChatUI } from "@/lib/chat-store";

const PROVIDER_LABELS: Record<AIProvider, string> = {
  anthropic: "Claude",
  openai: "GPT",
  google: "Gemini",
};

interface ModelSelectorProps {
  configuredProviders: Set<string>;
}

export function ModelSelector({ configuredProviders }: ModelSelectorProps) {
  const selectedProvider = useChatUI((s) => s.selectedProvider);
  const setProvider = useChatUI((s) => s.setProvider);

  const label = selectedProvider ? PROVIDER_LABELS[selectedProvider] : "Model";

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors cursor-pointer"
          aria-label="Select AI model"
        >
          {label}
          <ChevronDown className="size-3" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="min-w-36">
        {(Object.keys(PROVIDER_LABELS) as AIProvider[]).map((provider) => {
          const enabled = configuredProviders.has(provider);
          const isSelected = selectedProvider === provider;
          return (
            <DropdownMenuItem
              key={provider}
              disabled={!enabled}
              onClick={() => setProvider(provider)}
              className={cn(
                "cursor-pointer text-xs",
                isSelected && "font-semibold",
                !enabled && "cursor-default opacity-50",
              )}
            >
              <span className="flex-1">{PROVIDER_LABELS[provider]}</span>
              {!enabled && (
                <span className="text-[10px] text-muted-foreground ml-2">
                  No key
                </span>
              )}
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
