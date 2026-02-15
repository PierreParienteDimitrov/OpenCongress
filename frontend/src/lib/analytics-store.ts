"use client";

import { create } from "zustand";

// ─── Types ───────────────────────────────────────────────────────────

export type AnalyticsEventType =
  | "pageview"
  | "click"
  | "search"
  | "filter_change"
  | "bill_view"
  | "member_view"
  | "vote_view"
  | "share"
  | "signup"
  | "login"
  | "chat_open"
  | "follow";

export type AnalyticsPageType =
  | "bill"
  | "vote"
  | "member"
  | "chamber"
  | "committee"
  | "calendar"
  | "this-week"
  | "home"
  | "settings"
  | "login"
  | "documentation"
  | "";

interface QueuedEvent {
  event_type: AnalyticsEventType;
  timestamp: string;
  page_path: string;
  page_type: AnalyticsPageType;
  metadata: Record<string, unknown>;
  referrer: string;
}

interface EventBatchPayload {
  anonymous_id: string;
  session_id: string;
  user_id: string | null;
  events: QueuedEvent[];
  user_agent: string;
  referrer: string;
}

// ─── Constants ───────────────────────────────────────────────────────

const FLUSH_INTERVAL_MS = 5_000;
const FLUSH_THRESHOLD = 10;
const ANON_ID_KEY = "oc_anon_id";
const SESSION_ID_KEY = "oc_session_id";
const SESSION_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes
const SESSION_LAST_ACTIVITY_KEY = "oc_session_last";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// ─── Identity helpers ────────────────────────────────────────────────

function getOrCreateId(key: string): string {
  if (typeof window === "undefined") return "";
  let id = localStorage.getItem(key);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(key, id);
  }
  return id;
}

function getAnonymousId(): string {
  return getOrCreateId(ANON_ID_KEY);
}

function getSessionId(): string {
  if (typeof window === "undefined") return "";

  const lastActivity = localStorage.getItem(SESSION_LAST_ACTIVITY_KEY);
  const now = Date.now();

  // Session expired — start a new one
  if (lastActivity && now - parseInt(lastActivity, 10) > SESSION_TIMEOUT_MS) {
    const newId = crypto.randomUUID();
    localStorage.setItem(SESSION_ID_KEY, newId);
    localStorage.setItem(SESSION_LAST_ACTIVITY_KEY, String(now));
    return newId;
  }

  localStorage.setItem(SESSION_LAST_ACTIVITY_KEY, String(now));
  return getOrCreateId(SESSION_ID_KEY);
}

// ─── Store ───────────────────────────────────────────────────────────

interface AnalyticsState {
  queue: QueuedEvent[];
  userId: string | null;
  isInitialized: boolean;

  init: () => void;
  setUserId: (userId: string | null) => void;
  track: (
    eventType: AnalyticsEventType,
    options?: {
      pagePath?: string;
      pageType?: AnalyticsPageType;
      metadata?: Record<string, unknown>;
    }
  ) => void;
  flush: () => void;
}

export const useAnalyticsStore = create<AnalyticsState>((set, get) => {
  let flushTimer: ReturnType<typeof setInterval> | null = null;

  function startFlushTimer() {
    if (flushTimer) return;
    flushTimer = setInterval(() => {
      get().flush();
    }, FLUSH_INTERVAL_MS);
  }

  return {
    queue: [],
    userId: null,
    isInitialized: false,

    init: () => {
      if (get().isInitialized) return;

      // Respect Global Privacy Control
      if (
        typeof navigator !== "undefined" &&
        (navigator as Navigator & { globalPrivacyControl?: boolean })
          .globalPrivacyControl
      ) {
        return;
      }

      startFlushTimer();

      // Flush on page hide (tab close, navigate away)
      if (typeof document !== "undefined") {
        document.addEventListener("visibilitychange", () => {
          if (document.visibilityState === "hidden") {
            get().flush();
          }
        });
      }

      set({ isInitialized: true });
    },

    setUserId: (userId: string | null) => {
      set({ userId });
    },

    track: (eventType, options = {}) => {
      if (typeof window === "undefined") return;
      if (!get().isInitialized) return;

      const event: QueuedEvent = {
        event_type: eventType,
        timestamp: new Date().toISOString(),
        page_path: options.pagePath ?? window.location.pathname,
        page_type: options.pageType ?? "",
        metadata: options.metadata ?? {},
        referrer: document.referrer,
      };

      set((state) => {
        const newQueue = [...state.queue, event];

        if (newQueue.length >= FLUSH_THRESHOLD) {
          queueMicrotask(() => get().flush());
        }

        return { queue: newQueue };
      });
    },

    flush: () => {
      const { queue, userId } = get();
      if (queue.length === 0) return;

      // Move events out of queue immediately
      set({ queue: [] });

      const anonymousId = getAnonymousId();
      const sessionId = getSessionId();

      if (!anonymousId || !sessionId) return;

      const payload: EventBatchPayload = {
        anonymous_id: anonymousId,
        session_id: sessionId,
        user_id: userId,
        events: queue,
        user_agent: navigator.userAgent,
        referrer: document.referrer,
      };

      // Use sendBeacon when page is hiding (more reliable for unload)
      if (
        document.visibilityState === "hidden" &&
        typeof navigator.sendBeacon === "function"
      ) {
        const blob = new Blob([JSON.stringify(payload)], {
          type: "application/json",
        });
        navigator.sendBeacon(`${API_BASE_URL}/analytics/events/`, blob);
        return;
      }

      // Otherwise use fetch (fire-and-forget)
      fetch(`${API_BASE_URL}/analytics/events/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        keepalive: true,
      }).catch(() => {
        // Silently fail — analytics should never break the app
      });
    },
  };
});
