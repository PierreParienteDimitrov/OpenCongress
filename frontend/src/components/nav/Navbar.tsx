import Link from "next/link";
import { routes } from "@/lib/routes";
import { GridContainer } from "@/components/layout/GridContainer";
import { Button } from "@/components/ui/button";
import { ActiveLink } from "./ActiveLink";
import { ThemeToggle } from "./ThemeToggle";
import { MobileMenu } from "./MobileMenu";
import { navLinks } from "./NavLinks";

export function Navbar() {
  return (
    <nav className="sticky top-0 z-50 bg-nav">
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

        {/* Right: Theme toggle + Login + Mobile menu */}
        <div className="flex items-center gap-1">
          <ThemeToggle />
          <Button
            variant="ghost"
            className="hidden sm:inline-flex text-nav-foreground/70 hover:text-nav-foreground hover:bg-nav-foreground/10"
          >
            Login
          </Button>
          <MobileMenu />
        </div>
      </GridContainer>
    </nav>
  );
}
