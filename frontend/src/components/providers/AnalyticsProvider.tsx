"use client";

import { useEffect, useRef } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import { useSession } from "next-auth/react";
import {
  useAnalyticsStore,
  type AnalyticsPageType,
} from "@/lib/analytics-store";

/**
 * Derives page_type from a pathname.
 */
function derivePageType(pathname: string): AnalyticsPageType {
  if (pathname === "/") return "home";

  // Check member detail pages before chamber pages
  // e.g., /senate/S0001-john-doe or /house/H0001-jane-doe
  const memberDetailPattern = /^\/(senate|house)\/[A-Z]\d+/;
  if (memberDetailPattern.test(pathname)) return "member";

  if (pathname.startsWith("/senate")) return "chamber";
  if (pathname.startsWith("/house")) return "chamber";
  if (pathname.startsWith("/legislation/")) return "bill";
  if (pathname.startsWith("/vote/")) return "vote";
  if (pathname.startsWith("/committees")) return "committee";
  if (pathname.startsWith("/calendar")) return "calendar";
  if (pathname.startsWith("/this-week")) return "this-week";
  if (pathname.startsWith("/settings")) return "settings";
  if (pathname.startsWith("/login")) return "login";
  if (pathname.startsWith("/documentation")) return "documentation";

  return "";
}

export function AnalyticsProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { data: session } = useSession();
  const { init, setUserId, track } = useAnalyticsStore();
  const prevPathRef = useRef<string>("");

  // Initialize on mount
  useEffect(() => {
    init();
  }, [init]);

  // Sync user_id from session
  useEffect(() => {
    const userId = session?.user?.id ?? null;
    setUserId(userId ? String(userId) : null);
  }, [session?.user?.id, setUserId]);

  // Auto-track pageviews on route change
  useEffect(() => {
    const fullPath = searchParams.toString()
      ? `${pathname}?${searchParams.toString()}`
      : pathname;

    // Deduplicate: don't re-track if path hasn't changed
    if (fullPath === prevPathRef.current) return;
    prevPathRef.current = fullPath;

    const pageType = derivePageType(pathname);

    track("pageview", {
      pagePath: pathname,
      pageType,
      metadata: searchParams.toString()
        ? { search_params: searchParams.toString() }
        : {},
    });
  }, [pathname, searchParams, track]);

  return <>{children}</>;
}
