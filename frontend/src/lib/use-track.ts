"use client";

import { useCallback } from "react";
import { usePathname } from "next/navigation";
import {
  useAnalyticsStore,
  type AnalyticsEventType,
  type AnalyticsPageType,
} from "./analytics-store";

/**
 * Convenience hook for manual event tracking in components.
 *
 * Usage:
 *   const trackEvent = useTrack();
 *   trackEvent("click", { button_id: "share_bill", bill_id: "hr1234-119" });
 */
export function useTrack() {
  const { track } = useAnalyticsStore();
  const pathname = usePathname();

  const trackEvent = useCallback(
    (
      eventType: AnalyticsEventType,
      metadata?: Record<string, unknown>,
      pageType?: AnalyticsPageType
    ) => {
      track(eventType, {
        pagePath: pathname,
        pageType,
        metadata,
      });
    },
    [track, pathname]
  );

  return trackEvent;
}
