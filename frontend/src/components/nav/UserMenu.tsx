"use client";

import { useSession, signOut } from "next-auth/react";
import Link from "next/link";
import Image from "next/image";
import { LogIn, LogOut, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function UserMenu() {
  const { data: session, status } = useSession();

  if (status === "loading") {
    return (
      <div className="hidden sm:block size-8 rounded-full bg-nav-foreground/10 animate-pulse" />
    );
  }

  if (!session) {
    return (
      <Button
        variant="ghost"
        className="hidden sm:inline-flex text-nav-foreground/70 hover:text-nav-foreground hover:bg-nav-foreground/10"
        asChild
      >
        <Link href="/login">
          <LogIn className="mr-2 size-4" />
          Login
        </Link>
      </Button>
    );
  }

  const initial = (
    session.user.name?.[0] ||
    session.user.email?.[0] ||
    "U"
  ).toUpperCase();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className="hidden sm:inline-flex size-8 rounded-full p-0 hover:bg-nav-foreground/30 overflow-hidden cursor-pointer"
        >
          {session.user.image ? (
            <Image
              src={session.user.image}
              alt={session.user.name || "User"}
              width={32}
              height={32}
              className="rounded-full"
            />
          ) : (
            <span className="flex items-center justify-center size-8 rounded-full bg-nav-foreground/20 text-nav-foreground text-sm font-semibold">
              {initial}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem className="text-muted-foreground text-xs" disabled>
          {session.user.email}
        </DropdownMenuItem>
        <DropdownMenuItem asChild className="cursor-pointer">
          <Link href="/settings">
            <Settings className="mr-2 size-4" />
            Settings
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => signOut()} className="cursor-pointer">
          <LogOut className="mr-2 size-4" />
          Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
