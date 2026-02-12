"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

interface ActiveLinkProps {
  href: string;
  children: React.ReactNode;
  className?: string;
}

export function ActiveLink({ href, children, className }: ActiveLinkProps) {
  const pathname = usePathname();
  const isActive = pathname === href || pathname.startsWith(href + "/");

  return (
    <Link
      href={href}
      className={cn(
        "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
        "hover:bg-nav-foreground/10",
        isActive
          ? "bg-nav-foreground/15 text-nav-foreground"
          : "text-nav-foreground/70",
        className
      )}
    >
      {children}
    </Link>
  );
}
