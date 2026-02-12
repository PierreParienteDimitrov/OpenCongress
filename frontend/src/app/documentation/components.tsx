"use client";

import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface DocSectionProps {
  id: string;
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}

export function DocSection({ id, title, icon, children }: DocSectionProps) {
  return (
    <section id={id} className="scroll-mt-8">
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-accent/10 text-accent">
              {icon}
            </div>
            <h2 className="text-xl font-semibold text-foreground">
              {title}
            </h2>
          </div>
          <div className="text-muted-foreground leading-relaxed space-y-4">
            {children}
          </div>
        </CardContent>
      </Card>
    </section>
  );
}

interface DocSidebarLinkProps {
  href: string;
  label: string;
  isActive: boolean;
}

export function DocSidebarLink({ href, label, isActive }: DocSidebarLinkProps) {
  const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    const element = document.querySelector(href);
    if (element) {
      element.scrollIntoView({ behavior: "smooth" });
      window.history.pushState(null, "", href);
    }
  };

  return (
    <a
      href={href}
      onClick={handleClick}
      className={`block px-3 py-2 rounded-lg text-sm transition-colors ${
        isActive
          ? "bg-accent/10 text-accent font-medium"
          : "text-muted-foreground hover:bg-secondary hover:text-foreground"
      }`}
    >
      {label}
    </a>
  );
}

interface InfoCardProps {
  type?: "info" | "warning" | "success";
  title?: string;
  children: React.ReactNode;
}

export function InfoCard({ type = "info", title, children }: InfoCardProps) {
  const styles = {
    info: {
      bg: "bg-accent/10 border-accent/20",
      icon: "text-accent",
      title: "text-accent",
      text: "text-accent/80",
    },
    warning: {
      bg: "bg-amber-50 border-amber-100 dark:bg-amber-900/20 dark:border-amber-900/50",
      icon: "text-amber-500",
      title: "text-amber-800 dark:text-amber-300",
      text: "text-amber-700 dark:text-amber-300/80",
    },
    success: {
      bg: "bg-green-50 border-green-100 dark:bg-green-900/20 dark:border-green-900/50",
      icon: "text-green-500",
      title: "text-green-800 dark:text-green-300",
      text: "text-green-700 dark:text-green-300/80",
    },
  };

  const style = styles[type];

  return (
    <Alert className={cn(style.bg)}>
      <svg
        className={cn("h-5 w-5", style.icon)}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      {title && <AlertTitle className={cn(style.title)}>{title}</AlertTitle>}
      <AlertDescription className={cn(style.text)}>{children}</AlertDescription>
    </Alert>
  );
}

interface SourceBadgeProps {
  name: string;
  official?: boolean;
}

export function SourceBadge({ name, official = false }: SourceBadgeProps) {
  return (
    <Badge
      variant={official ? "default" : "secondary"}
      className={cn(
        "px-2.5 py-1",
        official && "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
      )}
    >
      {official && (
        <svg
          className="w-3.5 h-3.5"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fillRule="evenodd"
            d="M16.403 12.652a3 3 0 000-5.304 3 3 0 00-3.75-3.751 3 3 0 00-5.305 0 3 3 0 00-3.751 3.75 3 3 0 000 5.305 3 3 0 003.75 3.751 3 3 0 005.305 0 3 3 0 003.751-3.75zm-2.546-4.46a.75.75 0 00-1.214-.883l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
            clipRule="evenodd"
          />
        </svg>
      )}
      {name}
    </Badge>
  );
}

interface DocSidebarProps {
  sections: Array<{ id: string; label: string }>;
}

export function DocSidebar({ sections }: DocSidebarProps) {
  const [activeSection, setActiveSection] = useState<string>(sections[0]?.id || "");

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        });
      },
      {
        rootMargin: "-20% 0% -80% 0%",
      }
    );

    sections.forEach(({ id }) => {
      const element = document.getElementById(id);
      if (element) {
        observer.observe(element);
      }
    });

    return () => observer.disconnect();
  }, [sections]);

  return (
    <nav className="space-y-1">
      <p className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
        On this page
      </p>
      {sections.map(({ id, label }) => (
        <DocSidebarLink
          key={id}
          href={`#${id}`}
          label={label}
          isActive={activeSection === id}
        />
      ))}
    </nav>
  );
}
