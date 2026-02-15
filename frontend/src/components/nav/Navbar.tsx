import Link from "next/link";
import { routes } from "@/lib/routes";
import { GridContainer } from "@/components/layout/GridContainer";
import { ActiveLink } from "./ActiveLink";
import { MobileMenu } from "./MobileMenu";
import { UserMenu } from "./UserMenu";
import { NavChatButton } from "./NavChatButton";
import { NavRepAvatars } from "./NavRepAvatars";
import { NavSearchButton } from "./NavSearchButton";

import { navLinks } from "./NavLinks";

export function Navbar() {
  return (
    <nav className="sticky top-0 z-50 bg-nav border-b border-border">
      <GridContainer className="flex h-14 items-center justify-between">
        {/* Left: Logo + desktop links */}
        <div className="flex items-center gap-1">
          <Link
            href={routes.home}
            className="mr-4 text-lg font-bold text-nav-foreground"
          >
            OpenCongress
          </Link>

          {/* Desktop nav links — hidden below lg */}
          <div className="hidden lg:flex items-center gap-0.5">
            {navLinks.map((link) => (
              <ActiveLink key={link.href} href={link.href}>
                {link.label}
              </ActiveLink>
            ))}
          </div>
        </div>

        {/* Right: AI Bot + User menu + Mobile menu */}
        <div className="flex items-center gap-1.5">
          <NavSearchButton />
          <NavRepAvatars />
          <NavChatButton />
          <UserMenu />
          <MobileMenu />
        </div>
      </GridContainer>
    </nav>
  );
}
