/**
 * Centralized route definitions for type-safe, consistent navigation.
 */

export const routes = {
  home: "/",

  // Auth
  login: "/login",

  // Calendar
  calendar: {
    index: "/calendar",
    week: (weekDate: string) => `/calendar?week=${weekDate}`,
  },

  // This Week
  thisWeek: {
    index: "/this-week",
    week: (weekDate: string) => `/this-week?week=${weekDate}`,
    archive: (year: number, week: number) => `/this-week/${year}/${week}`,
  },

  // Chambers (members + seats + map)
  senate: {
    index: "/senate",
    detail: (bioguideId: string) => `/senate/${bioguideId}`,
    state: (stateCode: string) => `/senate/state/${stateCode}`,
  },
  house: {
    index: "/house",
    detail: (bioguideId: string) => `/house/${bioguideId}`,
    district: (districtId: string) => `/house/district/${districtId}`,
  },

  // Legislation
  legislation: {
    detail: (billId: string) => `/legislation/${billId}`,
  },

  // Votes
  vote: {
    detail: (voteId: string) => `/vote/${voteId}`,
  },

  // Settings
  settings: {
    index: "/settings",
    apiKeys: "/settings/api-keys",
    representatives: "/settings/representatives",
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
    ? routes.senate.detail(bioguideId)
    : routes.house.detail(bioguideId);
}
