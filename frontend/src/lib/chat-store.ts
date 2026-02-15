"use client";

import { create } from "zustand";
import type { PageContext } from "./chat-context";

export type { AIProvider } from "./chat-models";

const DEFAULT_SIDEBAR_WIDTH = 400;
const MIN_SIDEBAR_WIDTH = 320;
const MAX_SIDEBAR_WIDTH = 800;

interface ChatUIState {
  isOpen: boolean;
  isExpanded: boolean;
  selectedModel: string | null;
  sidebarWidth: number;
  pageContext: PageContext;
  toggle: () => void;
  open: () => void;
  close: () => void;
  toggleExpanded: () => void;
  collapse: () => void;
  setModel: (modelId: string) => void;
  setSidebarWidth: (width: number) => void;
  setPageContext: (context: PageContext) => void;
}

export const useChatUI = create<ChatUIState>((set) => ({
  isOpen: false,
  isExpanded: false,
  selectedModel: null,
  sidebarWidth: DEFAULT_SIDEBAR_WIDTH,
  pageContext: { type: "home", data: {} },
  toggle: () => set((s) => ({ isOpen: !s.isOpen })),
  open: () => set({ isOpen: true }),
  close: () => set({ isOpen: false, isExpanded: false }),
  toggleExpanded: () =>
    set((s) => ({ isExpanded: !s.isExpanded, isOpen: true })),
  collapse: () => set({ isExpanded: false }),
  setModel: (modelId) => set({ selectedModel: modelId }),
  setSidebarWidth: (width) =>
    set({
      sidebarWidth: Math.min(MAX_SIDEBAR_WIDTH, Math.max(MIN_SIDEBAR_WIDTH, width)),
    }),
  setPageContext: (context) => set({ pageContext: context }),
}));

export { MIN_SIDEBAR_WIDTH, MAX_SIDEBAR_WIDTH };
