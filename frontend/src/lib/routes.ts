/**
 * Centralized route definitions for type-safe, consistent navigation.
 */

export const routes = {
  home: "/",

  // Calendar
  calendar: {
    index: "/calendar",
    week: (weekDate: string) => `/calendar?week=${weekDate}`,
  },

  // This Week
  thisWeek: {
    index: "/this-week",
    archive: (year: number, week: number) => `/this-week/${year}/${week}`,
  },

  // Members
  senator: {
    index: "/senator",
    detail: (bioguideId: string) => `/senator/${bioguideId}`,
  },
  representative: {
    index: "/representative",
    detail: (bioguideId: string) => `/representative/${bioguideId}`,
  },

  // Legislation
  legislation: {
    detail: (billId: string) => `/legislation/${billId}`,
  },

  // Votes
  vote: {
    detail: (voteId: string) => `/vote/${voteId}`,
  },

  // Seat Maps (hemicycle)
  senateSeats: {
    index: "/senate-seats",
  },
  houseSeats: {
    index: "/house-seats",
  },

  // Documentation
  documentation: {
    index: "/documentation",
  },
} as const;

// Helper for member routes based on chamber
export function getMemberRoute(
  bioguideId: string,
  chamber: "senate" | "house"
): string {
  return chamber === "senate"
    ? routes.senator.detail(bioguideId)
    : routes.representative.detail(bioguideId);
}
