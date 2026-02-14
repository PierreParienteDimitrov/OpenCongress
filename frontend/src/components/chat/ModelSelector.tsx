"use client";

import { ChevronDown } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import { useChatUI } from "@/lib/chat-store";
import {
  PROVIDER_LABELS,
  getModelsByProvider,
  getModelById,
  type AIProvider,
} from "@/lib/chat-models";

interface ModelSelectorProps {
  configuredProviders: Set<string>;
}

export function ModelSelector({ configuredProviders }: ModelSelectorProps) {
  const selectedModel = useChatUI((s) => s.selectedModel);
  const setModel = useChatUI((s) => s.setModel);

  const modelDef = selectedModel ? getModelById(selectedModel) : null;
  const label = modelDef?.label ?? "Model";

  const modelsByProvider = getModelsByProvider();

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
      <DropdownMenuContent align="start" className="min-w-44">
        {Array.from(modelsByProvider.entries()).map(
          ([provider, models], groupIdx) => {
            const enabled = configuredProviders.has(provider);
            return (
              <div key={provider}>
                {groupIdx > 0 && <DropdownMenuSeparator />}
                <DropdownMenuLabel className="text-[10px] uppercase tracking-wider text-muted-foreground">
                  {PROVIDER_LABELS[provider as AIProvider]}
                  {!enabled && (
                    <span className="ml-1.5 normal-case tracking-normal">
                      — no key
                    </span>
                  )}
                </DropdownMenuLabel>
                <DropdownMenuGroup>
                  {models.map((model) => {
                    const isSelected = selectedModel === model.id;
                    return (
                      <DropdownMenuItem
                        key={model.id}
                        disabled={!enabled}
                        onClick={() => setModel(model.id)}
                        className={cn(
                          "cursor-pointer text-xs",
                          isSelected && "font-semibold",
                          !enabled && "cursor-default opacity-50",
                        )}
                      >
                        {model.label}
                      </DropdownMenuItem>
                    );
                  })}
                </DropdownMenuGroup>
              </div>
            );
          },
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
