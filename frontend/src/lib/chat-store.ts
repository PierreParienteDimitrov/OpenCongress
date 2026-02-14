"use client";

import { create } from "zustand";

export type { AIProvider } from "./chat-models";

interface ChatUIState {
  isOpen: boolean;
  isExpanded: boolean;
  selectedModel: string | null;
  toggle: () => void;
  open: () => void;
  close: () => void;
  toggleExpanded: () => void;
  collapse: () => void;
  setModel: (modelId: string) => void;
}

export const useChatUI = create<ChatUIState>((set) => ({
  isOpen: false,
  isExpanded: false,
  selectedModel: null,
  toggle: () => set((s) => ({ isOpen: !s.isOpen })),
  open: () => set({ isOpen: true }),
  close: () => set({ isOpen: false, isExpanded: false }),
  toggleExpanded: () =>
    set((s) => ({ isExpanded: !s.isExpanded, isOpen: true })),
  collapse: () => set({ isExpanded: false }),
  setModel: (modelId) => set({ selectedModel: modelId }),
}));
