/**
 * Centralized route definitions for type-safe, consistent navigation.
 */

import { slugifyName } from "@/lib/utils";

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
    detail: (bioguideId: string, fullName?: string) =>
      fullName
        ? `/senate/${bioguideId}-${slugifyName(fullName)}`
        : `/senate/${bioguideId}`,
    state: (stateCode: string) => `/senate/state/${stateCode}`,
  },
  house: {
    index: "/house",
    detail: (bioguideId: string, fullName?: string) =>
      fullName
        ? `/house/${bioguideId}-${slugifyName(fullName)}`
        : `/house/${bioguideId}`,
    district: (districtId: string) => `/house/district/${districtId}`,
  },

  // Committees
  committees: {
    index: "/committees",
    detail: (committeeId: string, name?: string) =>
      name
        ? `/committees/${committeeId}-${slugifyName(name)}`
        : `/committees/${committeeId}`,
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
};

// Helper for member routes based on chamber
export function getMemberRoute(
  bioguideId: string,
  chamber: "senate" | "house",
  fullName?: string
): string {
  return chamber === "senate"
    ? routes.senate.detail(bioguideId, fullName)
    : routes.house.detail(bioguideId, fullName);
}
