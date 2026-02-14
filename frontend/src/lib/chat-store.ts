"use client";

import { create } from "zustand";

export type AIProvider = "anthropic" | "openai" | "google";

interface ChatUIState {
  isOpen: boolean;
  isExpanded: boolean;
  selectedProvider: AIProvider | null;
  toggle: () => void;
  open: () => void;
  close: () => void;
  toggleExpanded: () => void;
  collapse: () => void;
  setProvider: (provider: AIProvider) => void;
}

export const useChatUI = create<ChatUIState>((set) => ({
  isOpen: false,
  isExpanded: false,
  selectedProvider: null,
  toggle: () => set((s) => ({ isOpen: !s.isOpen })),
  open: () => set({ isOpen: true }),
  close: () => set({ isOpen: false, isExpanded: false }),
  toggleExpanded: () =>
    set((s) => ({ isExpanded: !s.isExpanded, isOpen: true })),
  collapse: () => set({ isExpanded: false }),
  setProvider: (provider) => set({ selectedProvider: provider }),
}));
