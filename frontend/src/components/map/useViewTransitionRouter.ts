"use client";

import { useRouter } from "next/navigation";
import { useCallback } from "react";

export function useViewTransitionRouter() {
  const router = useRouter();

  const push = useCallback(
    (href: string) => {
      if (
        typeof document !== "undefined" &&
        "startViewTransition" in document
      ) {
        (document as unknown as { startViewTransition: (cb: () => void) => void })
          .startViewTransition(() => {
            router.push(href);
          });
      } else {
        router.push(href);
      }
    },
    [router]
  );

  return { push, router };
}
