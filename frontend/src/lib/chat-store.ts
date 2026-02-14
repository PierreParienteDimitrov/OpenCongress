"use client";

import { create } from "zustand";

interface ChatUIState {
  isOpen: boolean;
  isExpanded: boolean;
  toggle: () => void;
  open: () => void;
  close: () => void;
  toggleExpanded: () => void;
  collapse: () => void;
}

export const useChatUI = create<ChatUIState>((set) => ({
  isOpen: false,
  isExpanded: false,
  toggle: () => set((s) => ({ isOpen: !s.isOpen })),
  open: () => set({ isOpen: true }),
  close: () => set({ isOpen: false, isExpanded: false }),
  toggleExpanded: () =>
    set((s) => ({ isExpanded: !s.isExpanded, isOpen: true })),
  collapse: () => set({ isExpanded: false }),
}));
