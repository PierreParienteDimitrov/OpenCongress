"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";
import { useSession, signOut } from "next-auth/react";
import Link from "next/link";
import { Menu, LogOut, MapPin, Settings } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetFooter,
  SheetTrigger,
} from "@/components/ui/sheet";
import { navLinks } from "./NavLinks";

export function MobileMenu() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  const { data: session } = useSession();

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden text-nav-foreground/70 hover:text-nav-foreground hover:bg-nav-foreground/10"
        >
          <Menu className="size-5" />
          <span className="sr-only">Open menu</span>
        </Button>
      </SheetTrigger>
      <SheetContent
        side="right"
        showCloseButton
        className="w-72 bg-nav border-nav-foreground/10 p-0 gap-0"
      >
        <SheetHeader className="border-b border-nav-foreground/10 px-4 py-4">
          <SheetTitle className="text-nav-foreground font-bold">
            OpenCongress
          </SheetTitle>
        </SheetHeader>

        <nav className="flex flex-col p-4 gap-1">
          {navLinks.map((link) => {
            const isActive =
              pathname === link.href ||
              pathname.startsWith(link.href + "/");
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setOpen(false)}
                className={cn(
                  "px-3 py-2.5 rounded-md text-sm font-medium transition-colors",
                  isActive
                    ? "bg-nav-foreground/15 text-nav-foreground"
                    : "text-nav-foreground/70 hover:bg-nav-foreground/10 hover:text-nav-foreground"
                )}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        <SheetFooter className="border-t border-nav-foreground/10 p-4">
          {session ? (
            <div className="w-full space-y-2">
              <p className="text-xs text-nav-foreground/60 truncate px-1">
                {session.user.email}
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  className="flex-1 border-nav-foreground/20 text-nav-foreground bg-transparent hover:bg-nav-foreground/10 cursor-pointer"
                  asChild
                >
                  <Link href="/settings" onClick={() => setOpen(false)}>
                    <Settings className="mr-2 size-4" />
                    Settings
                  </Link>
                </Button>
                <Button
                  variant="outline"
                  className="flex-1 border-nav-foreground/20 text-nav-foreground bg-transparent hover:bg-nav-foreground/10 cursor-pointer"
                  asChild
                >
                  <Link
                    href="/settings/representatives"
                    onClick={() => setOpen(false)}
                  >
                    <MapPin className="mr-2 size-4" />
                    My Rep
                  </Link>
                </Button>
              </div>
              <Button
                variant="outline"
                className="w-full border-nav-foreground/20 text-nav-foreground bg-transparent hover:bg-nav-foreground/10 cursor-pointer"
                onClick={() => {
                  setOpen(false);
                  signOut();
                }}
              >
                <LogOut className="mr-2 size-4" />
                Sign out
              </Button>
            </div>
          ) : (
            <Button
              variant="outline"
              className="w-full border-nav-foreground/20 text-nav-foreground bg-transparent hover:bg-nav-foreground/10"
              asChild
            >
              <Link href="/login" onClick={() => setOpen(false)}>
                Login
              </Link>
            </Button>
          )}
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
