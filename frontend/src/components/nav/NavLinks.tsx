import { routes } from "@/lib/routes";

export const navLinks = [
  { label: "Senate", href: routes.senate.index },
  { label: "House", href: routes.house.index },
  { label: "Docs", href: routes.documentation.index },
] as const;
