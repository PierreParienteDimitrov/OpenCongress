import { routes } from "@/lib/routes";

export const navLinks = [
  { label: "This Week", href: routes.thisWeek.index },
  { label: "Calendar", href: routes.calendar.index },
  { label: "Senators", href: routes.senator.index },
  { label: "Representatives", href: routes.representative.index },
  { label: "Senate Seats", href: routes.senateSeats.index },
  { label: "House Seats", href: routes.houseSeats.index },
  { label: "Docs", href: routes.documentation.index },
] as const;
