"use client";

import { useEffect, useCallback, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useSession } from "next-auth/react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  Settings,
  LogIn,
  X,
  Maximize2,
  Minimize2,
  RotateCcw,
} from "lucide-react";
import Link from "next/link";
import { motion, AnimatePresence, useDragControls } from "framer-motion";
import {
  useLocalRuntime,
  AssistantRuntimeProvider,
  useAui,
  useAuiState,
} from "@assistant-ui/react";
import { Button } from "@/components/ui/button";
import { Thread } from "@/components/assistant-ui/thread";
import { fetchAPIKeys, type ConfiguredAPIKey } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import { useChatUI } from "@/lib/chat-store";
import { CHAT_MODELS, getModelById } from "@/lib/chat-models";
import { createDjangoChatAdapter } from "./ChatModelAdapter";
import { ModelSelector } from "./ModelSelector";

// ── Panel constants ──
const DEFAULT_WIDTH = 400;
const DEFAULT_HEIGHT = 560;
const MIN_WIDTH = 320;
const MIN_HEIGHT = 400;
const PANEL_MARGIN = 24;

function getDefaultPosition(width = DEFAULT_WIDTH, height = DEFAULT_HEIGHT) {
  if (typeof window === "undefined") return { x: 0, y: 0 };
  return {
    x: window.innerWidth - width - PANEL_MARGIN,
    y: window.innerHeight - height - PANEL_MARGIN - 72,
  };
}

// ── Clear chat button (must be inside AssistantRuntimeProvider) ──
function ClearChatButton() {
  const aui = useAui();
  const isEmpty = useAuiState((s) => s.thread.isEmpty);

  if (isEmpty) return null;

  return (
    <Button
      variant="ghost"
      size="icon"
      className="size-7 cursor-pointer text-muted-foreground"
      onClick={(e) => {
        e.stopPropagation();
        aui.threads().switchToNewThread();
      }}
      title="Clear chat"
    >
      <RotateCcw className="size-3.5" />
    </Button>
  );
}

// ── Main component ──
export function ChatInterface() {
  const { data: session } = useSession();
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const pageContext = useChatUI((s) => s.pageContext);
  const isOpen = useChatUI((s) => s.isOpen);
  const isExpanded = useChatUI((s) => s.isExpanded);
  const storedModel = useChatUI((s) => s.selectedModel);
  const setModel = useChatUI((s) => s.setModel);
  const openChat = useChatUI((s) => s.open);
  const closeChat = useChatUI((s) => s.close);
  const toggleExpanded = useChatUI((s) => s.toggleExpanded);

  // Panel state (floating mode only)
  const [panelSize, setPanelSize] = useState({
    width: DEFAULT_WIDTH,
    height: DEFAULT_HEIGHT,
  });
  const [panelPosition, setPanelPosition] = useState<{
    x: number;
    y: number;
  } | null>(null);
  const dragControls = useDragControls();
  const isResizing = useRef(false);

  const { data: apiKeys = [] } = useQuery<ConfiguredAPIKey[]>({
    queryKey: ["api-keys"],
    queryFn: fetchAPIKeys,
    enabled: !!session,
  });

  // Set of configured provider names (for enabling/disabling in dropdown)
  const configuredProviders = useMemo(
    () => new Set(apiKeys.map((k) => k.provider)),
    [apiKeys],
  );

  // Auto-select first available model if none selected or current is invalid
  useEffect(() => {
    if (apiKeys.length === 0) return;
    const currentDef = storedModel ? getModelById(storedModel) : null;
    if (!currentDef || !configuredProviders.has(currentDef.provider)) {
      const firstAvailable = CHAT_MODELS.find((m) =>
        configuredProviders.has(m.provider),
      );
      if (firstAvailable) setModel(firstAvailable.id);
    }
  }, [apiKeys, storedModel, configuredProviders, setModel]);

  // Set default position on first open (client-side only)
  const panelPositionResolved = useMemo(() => {
    if (isOpen && !panelPosition) {
      return getDefaultPosition(panelSize.width, panelSize.height);
    }
    return panelPosition;
  }, [isOpen, panelPosition, panelSize.width, panelSize.height]);

  // Open chat + clean up the chatOpen URL param after login redirect
  useEffect(() => {
    if (searchParams.get("chatOpen") === "true") {
      openChat();
      const params = new URLSearchParams(searchParams.toString());
      params.delete("chatOpen");
      const newQuery = params.toString();
      router.replace(newQuery ? `${pathname}?${newQuery}` : pathname, {
        scroll: false,
      });
    }
  }, [searchParams, router, pathname, openChat]);

  // Viewport resize safety — clamp panel position
  useEffect(() => {
    const handleResize = () => {
      setPanelPosition((prev) => {
        if (!prev) return prev;
        return {
          x: Math.min(prev.x, window.innerWidth - 100),
          y: Math.min(prev.y, window.innerHeight - 100),
        };
      });
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Build login URL
  const buildLoginUrl = useCallback(() => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("chatOpen", "true");
    const returnUrl = `${pathname}?${params.toString()}`;
    return `/login?callbackUrl=${encodeURIComponent(returnUrl)}`;
  }, [pathname, searchParams]);

  // Resize handler (floating mode only)
  const startResize = useCallback(
    (e: React.MouseEvent, direction: "se" | "e" | "s") => {
      e.preventDefault();
      e.stopPropagation();
      isResizing.current = true;

      const startX = e.clientX;
      const startY = e.clientY;
      const startWidth = panelSize.width;
      const startHeight = panelSize.height;

      document.body.classList.add("select-none");

      const onMouseMove = (ev: MouseEvent) => {
        const dx = ev.clientX - startX;
        const dy = ev.clientY - startY;

        setPanelSize({
          width:
            direction === "s"
              ? startWidth
              : Math.max(MIN_WIDTH, startWidth + dx),
          height:
            direction === "e"
              ? startHeight
              : Math.max(MIN_HEIGHT, startHeight + dy),
        });
      };

      const onMouseUp = () => {
        isResizing.current = false;
        document.body.classList.remove("select-none");
        document.removeEventListener("mousemove", onMouseMove);
        document.removeEventListener("mouseup", onMouseUp);
      };

      document.addEventListener("mousemove", onMouseMove);
      document.addEventListener("mouseup", onMouseUp);
    },
    [panelSize.width, panelSize.height],
  );

  // Context label for welcome message
  const contextLabel = useMemo(() => {
    switch (pageContext.type) {
      case "bill":
        return "this bill";
      case "vote":
        return "this vote";
      case "member":
        return "this member";
      default:
        return "congressional activity";
    }
  }, [pageContext.type]);

  // assistant-ui adapter + runtime
  const adapter = useMemo(() => {
    if (!storedModel) return null;
    const modelDef = getModelById(storedModel);
    if (!modelDef) return null;
    return createDjangoChatAdapter(modelDef.provider, storedModel, pageContext);
  }, [storedModel, pageContext]);

  const runtime = useLocalRuntime(adapter!);

  const hasKeys = apiKeys.length > 0;
  const showChat = session && hasKeys && adapter;
  const isMobile = typeof window !== "undefined" && window.innerWidth < 640;

  // ── Shared header + thread content (rendered inside both modes) ──
  const headerProps = {
    isMobile,
    isExpanded,
    onToggleExpand: () => toggleExpanded(),
    onClose: closeChat,
    onPointerDown: (e: React.PointerEvent) => {
      if (!isMobile && !isExpanded) dragControls.start(e);
    },
  };

  // ── Non-authenticated / no-keys fallback (no runtime needed) ──
  if (!showChat) {
    const fallbackContent = (
      <>
        <ChatPanelHeader showClearButton={false} {...headerProps} />
        {!session ? (
          <div className="flex flex-1 items-center justify-center p-6">
            <div className="text-center space-y-3">
              <LogIn className="mx-auto size-10 text-muted-foreground/40" />
              <div>
                <p className="font-medium text-sm">Sign in to get started</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Log in with your account to use the AI assistant.
                </p>
              </div>
              <Button asChild size="sm" variant="outline">
                <Link
                  href={buildLoginUrl()}
                  onClick={closeChat}
                  className="cursor-pointer"
                >
                  Sign in
                </Link>
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex flex-1 items-center justify-center p-6">
            <div className="text-center space-y-3">
              <Settings className="mx-auto size-10 text-muted-foreground/40" />
              <div>
                <p className="font-medium text-sm">No API keys configured</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Add at least one AI provider API key in settings to use the
                  chat.
                </p>
              </div>
              <Button asChild size="sm" variant="outline">
                <Link
                  href="/settings"
                  onClick={closeChat}
                  className="cursor-pointer"
                >
                  Go to Settings
                </Link>
              </Button>
            </div>
          </div>
        )}
      </>
    );

    return (
      <ChatShell
        isOpen={isOpen}
        isExpanded={isExpanded}
        isMobile={isMobile}
        panelSize={panelSize}
        panelPositionResolved={panelPositionResolved}
        dragControls={dragControls}
        setPanelPosition={setPanelPosition}
        startResize={startResize}
      >
        {fallbackContent}
      </ChatShell>
    );
  }

  // ── Authenticated chat: runtime wraps both modes so conversation persists ──
  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <ChatShell
        isOpen={isOpen}
        isExpanded={isExpanded}
        isMobile={isMobile}
        panelSize={panelSize}
        panelPositionResolved={panelPositionResolved}
        dragControls={dragControls}
        setPanelPosition={setPanelPosition}
        startResize={startResize}
      >
        <ChatPanelHeader showClearButton {...headerProps} />
        <Thread
          contextLabel={contextLabel}
          composerFooter={
            <ModelSelector configuredProviders={configuredProviders} />
          }
        />
      </ChatShell>
    </AssistantRuntimeProvider>
  );
}

// ── Shell: handles sidebar-portal vs floating-panel rendering ──
function ChatShell({
  isOpen,
  isExpanded,
  isMobile,
  panelSize,
  panelPositionResolved,
  dragControls,
  setPanelPosition,
  startResize,
  children,
}: {
  isOpen: boolean;
  isExpanded: boolean;
  isMobile: boolean;
  panelSize: { width: number; height: number };
  panelPositionResolved: { x: number; y: number } | null;
  dragControls: ReturnType<typeof useDragControls>;
  setPanelPosition: React.Dispatch<
    React.SetStateAction<{ x: number; y: number } | null>
  >;
  startResize: (e: React.MouseEvent, direction: "se" | "e" | "s") => void;
  children: React.ReactNode;
}) {
  const sidebarSlot =
    typeof document !== "undefined"
      ? document.getElementById("chat-sidebar-slot")
      : null;

  // ── Sidebar mode: portal into the sidebar slot ──
  if (isOpen && isExpanded && sidebarSlot) {
    return createPortal(
      <div className="flex h-full flex-col overflow-hidden bg-muted/90">
        {children}
      </div>,
      sidebarSlot,
    );
  }

  // ── Floating mode ──
  return (
    <AnimatePresence>
      {isOpen && panelPositionResolved && (
        <motion.div
          drag={!isMobile}
          dragControls={dragControls}
          dragListener={false}
          dragMomentum={false}
          dragConstraints={{
            left: 0,
            top: 0,
            right: Math.max(0, window.innerWidth - panelSize.width),
            bottom: Math.max(0, window.innerHeight - panelSize.height),
          }}
          onDragEnd={(_e, info) => {
            setPanelPosition((prev) => {
              if (!prev) return prev;
              return {
                x: prev.x + info.offset.x,
                y: prev.y + info.offset.y,
              };
            });
          }}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.15, ease: "easeOut" }}
          style={
            isMobile
              ? { position: "fixed" as const, inset: 0, zIndex: 50 }
              : {
                  position: "fixed" as const,
                  left: panelPositionResolved.x,
                  top: panelPositionResolved.y,
                  width: panelSize.width,
                  height: panelSize.height,
                  zIndex: 50,
                }
          }
          className={cn(
            "flex flex-col rounded-lg border bg-muted/90 shadow-xl overflow-hidden",
            isMobile && "rounded-none",
          )}
        >
          {children}

          {/* Resize handles (desktop only) */}
          {!isMobile && (
            <>
              {/* SE corner — diagonal resize with grip dots */}
              <div
                onMouseDown={(e) => startResize(e, "se")}
                className="absolute bottom-0 right-0 size-4 cursor-se-resize"
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 16 16"
                  className="text-muted-foreground/40"
                >
                  <circle cx="12" cy="12" r="1.5" fill="currentColor" />
                  <circle cx="8" cy="12" r="1.5" fill="currentColor" />
                  <circle cx="12" cy="8" r="1.5" fill="currentColor" />
                </svg>
              </div>
              {/* E edge — width only */}
              <div
                onMouseDown={(e) => startResize(e, "e")}
                className="absolute top-0 right-0 w-1.5 h-full cursor-e-resize"
              />
              {/* S edge — height only */}
              <div
                onMouseDown={(e) => startResize(e, "s")}
                className="absolute bottom-0 left-0 w-full h-1.5 cursor-s-resize"
              />
            </>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// ── Extracted header component ──
function ChatPanelHeader({
  showClearButton,
  isMobile,
  isExpanded,
  onToggleExpand,
  onClose,
  onPointerDown,
}: {
  showClearButton: boolean;
  isMobile: boolean;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onClose: () => void;
  onPointerDown: (e: React.PointerEvent) => void;
}) {
  return (
    <div
      onPointerDown={onPointerDown}
      className={cn(
        "flex h-14 items-center justify-between border-b px-3 shrink-0",
        !isMobile && !isExpanded && "cursor-grab active:cursor-grabbing",
      )}
    >
      <h2 className="text-sm font-semibold select-none">AI Assistant</h2>
      <div className="flex items-center gap-0.5">
        {showClearButton && <ClearChatButton />}
        {!isMobile && (
          <Button
            variant="ghost"
            size="icon"
            className="size-7 cursor-pointer text-muted-foreground"
            onClick={(e) => {
              e.stopPropagation();
              onToggleExpand();
            }}
            title={isExpanded ? "Collapse to panel" : "Expand to sidebar"}
          >
            {isExpanded ? (
              <Minimize2 className="size-3.5" />
            ) : (
              <Maximize2 className="size-3.5" />
            )}
          </Button>
        )}
        <Button
          variant="ghost"
          size="icon"
          className="size-7 cursor-pointer text-muted-foreground"
          onClick={(e) => {
            e.stopPropagation();
            onClose();
          }}
          title="Close"
        >
          <X className="size-3.5" />
        </Button>
      </div>
    </div>
  );
}
