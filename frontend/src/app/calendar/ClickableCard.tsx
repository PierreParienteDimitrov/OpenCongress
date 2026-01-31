"use client";

import { useRouter } from "next/navigation";
import type { ReactNode } from "react";

interface ClickableCardProps {
  href: string | null;
  itemId: string;
  itemType: "vote" | "bill";
  children: ReactNode;
  className?: string;
}

export function ClickableCard({ href, itemId, itemType, children, className }: ClickableCardProps) {
  const router = useRouter();

  const handleClick = () => {
    console.log("=== ClickableCard clicked ===");
    console.log("itemType:", itemType);
    console.log("itemId:", itemId);
    console.log("href:", href);
    if (href) {
      console.log("Navigating to:", href);
      router.push(href);
    } else {
      console.log("No href provided, not navigating");
    }
  };

  return (
    <div
      onClick={handleClick}
      style={{ cursor: "pointer" }}
      className={className || ""}
      role="link"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          handleClick();
        }
      }}
    >
      {children}
    </div>
  );
}
