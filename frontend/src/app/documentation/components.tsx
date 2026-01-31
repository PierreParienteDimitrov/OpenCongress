"use client";

import { useEffect, useState } from "react";

interface DocSectionProps {
  id: string;
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}

export function DocSection({ id, title, icon, children }: DocSectionProps) {
  return (
    <section id={id} className="scroll-mt-8">
      <div className="bg-white rounded-lg shadow-sm p-6 dark:bg-zinc-900">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-lg bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
            {icon}
          </div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-zinc-50">
            {title}
          </h2>
        </div>
        <div className="text-gray-600 dark:text-zinc-400 leading-relaxed space-y-4">
          {children}
        </div>
      </div>
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
          ? "bg-blue-50 text-blue-700 font-medium dark:bg-blue-900/30 dark:text-blue-400"
          : "text-gray-600 hover:bg-gray-100 hover:text-gray-900 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-zinc-200"
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
      bg: "bg-blue-50 border-blue-100 dark:bg-blue-900/20 dark:border-blue-900/50",
      icon: "text-blue-500",
      title: "text-blue-800 dark:text-blue-300",
      text: "text-blue-700 dark:text-blue-300/80",
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
    <div className={`rounded-lg border p-4 ${style.bg}`}>
      <div className="flex items-start gap-3">
        <svg
          className={`w-5 h-5 mt-0.5 flex-shrink-0 ${style.icon}`}
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
        <div>
          {title && (
            <p className={`font-medium mb-1 ${style.title}`}>{title}</p>
          )}
          <div className={`text-sm ${style.text}`}>{children}</div>
        </div>
      </div>
    </div>
  );
}

interface SourceBadgeProps {
  name: string;
  official?: boolean;
}

export function SourceBadge({ name, official = false }: SourceBadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
        official
          ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
          : "bg-gray-100 text-gray-700 dark:bg-zinc-800 dark:text-zinc-300"
      }`}
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
    </span>
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
      <p className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider dark:text-zinc-500">
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
