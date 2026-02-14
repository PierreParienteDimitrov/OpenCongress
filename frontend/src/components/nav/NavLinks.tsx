import { routes } from "@/lib/routes";

export const navLinks = [
  { label: "Senate", href: routes.senate.index },
  { label: "House", href: routes.house.index },
] as const;
