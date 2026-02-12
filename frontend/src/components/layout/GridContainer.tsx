import { type ReactNode } from "react";

interface GridContainerProps {
  children: ReactNode;
  className?: string;
  /** Render as a 12-column CSS grid instead of a plain container */
  asGrid?: boolean;
}

/**
 * Responsive container that applies the 12-column grid system margins and max-width.
 *
 * - Mobile (<768px):  16px margins, 16px gutters, fluid
 * - Tablet (768px+):  24px margins, 20px gutters, fluid
 * - Desktop (1024px+): 32px margins, 24px gutters, fluid
 * - Wide (1280px+):   auto margins, 24px gutters, max 1200px
 * - XL (1440px+):     auto margins, 32px gutters, max 1360px
 *
 * Use `asGrid` to get a 12-column CSS grid directly on this element.
 */
export function GridContainer({
  children,
  className = "",
  asGrid = false,
}: GridContainerProps) {
  return (
    <div
      className={`grid-container ${asGrid ? "grid-container--grid" : ""} ${className}`.trim()}
    >
      {children}
    </div>
  );
}
