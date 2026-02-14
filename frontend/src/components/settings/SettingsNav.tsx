"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { KeyRound, MapPin } from "lucide-react";
import { cn } from "@/lib/utils";
import { routes } from "@/lib/routes";

const navItems = [
  {
    href: routes.settings.apiKeys,
    label: "API Keys",
    icon: KeyRound,
  },
  {
    href: routes.settings.representatives,
    label: "My Representatives",
    icon: MapPin,
  },
];

export function SettingsNav() {
  const pathname = usePathname();

  return (
    <nav className="flex flex-row gap-1 md:flex-col">
      {navItems.map((item) => {
        const isActive = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors cursor-pointer",
              isActive
                ? "bg-accent text-accent-foreground"
                : "text-muted-foreground hover:bg-accent/50 hover:text-foreground",
            )}
          >
            <item.icon className="size-4" />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
