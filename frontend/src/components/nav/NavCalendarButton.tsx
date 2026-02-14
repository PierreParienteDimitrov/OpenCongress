"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { CalendarDays } from "lucide-react";
import { cn } from "@/lib/utils";
import { routes } from "@/lib/routes";
import { Button } from "@/components/ui/button";

export function NavCalendarButton() {
  const pathname = usePathname();
  const isActive =
    pathname === routes.calendar.index ||
    pathname.startsWith(routes.calendar.index + "/");

  return (
    <Button
      variant="ghost"
      size="icon"
      asChild
      className={cn(
        "hidden lg:inline-flex cursor-pointer",
        isActive
          ? "bg-nav-foreground/15 text-nav-foreground"
          : "text-nav-foreground/70 hover:text-nav-foreground hover:bg-nav-foreground/10",
      )}
    >
      <Link href={routes.calendar.index} aria-label="Calendar">
        <CalendarDays className="size-4" />
      </Link>
    </Button>
  );
}
