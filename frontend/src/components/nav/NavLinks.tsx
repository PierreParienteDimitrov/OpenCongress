import { routes } from "@/lib/routes";

export const navLinks = [
  { label: "Senate", href: routes.senate.index },
  { label: "House", href: routes.house.index },
  { label: "Committees", href: routes.committees.index },
  { label: "Calendar", href: routes.calendar.index },
] as const;
