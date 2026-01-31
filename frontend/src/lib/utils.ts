/**
 * Utility functions for formatting and display.
 */

import type { VotePosition, VoteResult } from "@/types";

// Party utilities
export function getPartyName(party: string): string {
  const parties: Record<string, string> = {
    D: "Democrat",
    R: "Republican",
    I: "Independent",
  };
  return parties[party] || party;
}

export function getPartyColor(party: string): string {
  const colors: Record<string, string> = {
    D: "#2563eb", // blue-600
    R: "#dc2626", // red-600
    I: "#7c3aed", // violet-600
  };
  return colors[party] || "#6b7280"; // gray-500
}

export function getPartyBgColor(party: string): string {
  const colors: Record<string, string> = {
    D: "bg-blue-100 text-blue-800",
    R: "bg-red-100 text-red-800",
    I: "bg-violet-100 text-violet-800",
  };
  return colors[party] || "bg-gray-100 text-gray-800";
}

// Chamber utilities
export function getChamberName(chamber: string): string {
  const chambers: Record<string, string> = {
    house: "House of Representatives",
    senate: "Senate",
  };
  return chambers[chamber] || chamber;
}

export function getChamberShortName(chamber: string): string {
  const chambers: Record<string, string> = {
    house: "House",
    senate: "Senate",
  };
  return chambers[chamber] || chamber;
}

// Vote position utilities
export function getPositionLabel(position: VotePosition): string {
  const labels: Record<VotePosition, string> = {
    yea: "Yea",
    nay: "Nay",
    present: "Present",
    not_voting: "Not Voting",
  };
  return labels[position] || position;
}

export function getPositionColor(position: VotePosition): string {
  const colors: Record<VotePosition, string> = {
    yea: "text-green-600",
    nay: "text-red-600",
    present: "text-yellow-600",
    not_voting: "text-gray-400",
  };
  return colors[position] || "text-gray-600";
}

export function getPositionBgColor(position: VotePosition): string {
  const colors: Record<VotePosition, string> = {
    yea: "bg-green-100 text-green-800",
    nay: "bg-red-100 text-red-800",
    present: "bg-yellow-100 text-yellow-800",
    not_voting: "bg-gray-100 text-gray-500",
  };
  return colors[position] || "bg-gray-100 text-gray-800";
}

// Vote result utilities
export function getResultLabel(result: VoteResult): string {
  const labels: Record<VoteResult, string> = {
    passed: "Passed",
    failed: "Failed",
    agreed: "Agreed To",
    rejected: "Rejected",
  };
  return labels[result] || result;
}

export function getResultColor(result: VoteResult): string {
  const colors: Record<VoteResult, string> = {
    passed: "text-green-600",
    failed: "text-red-600",
    agreed: "text-green-600",
    rejected: "text-red-600",
  };
  return colors[result] || "text-gray-600";
}

export function getResultBgColor(result: VoteResult): string {
  const colors: Record<VoteResult, string> = {
    passed: "bg-green-100 text-green-800",
    failed: "bg-red-100 text-red-800",
    agreed: "bg-green-100 text-green-800",
    rejected: "bg-red-100 text-red-800",
  };
  return colors[result] || "bg-gray-100 text-gray-800";
}

// Date utilities
export function formatDate(dateString: string | null): string {
  if (!dateString) return "";
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatDateLong(dateString: string | null): string {
  if (!dateString) return "";
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export function formatTime(timeString: string | null): string {
  if (!timeString) return "";
  const [hours, minutes] = timeString.split(":");
  const date = new Date();
  date.setHours(parseInt(hours, 10));
  date.setMinutes(parseInt(minutes, 10));
  return date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

// Week utilities for calendar
export function getWeekStart(date: Date): Date {
  const d = new Date(date);
  const day = d.getDay();
  const diff = d.getDate() - day; // Sunday as start
  d.setDate(diff);
  d.setHours(0, 0, 0, 0);
  return d;
}

export function getWeekEnd(date: Date): Date {
  const start = getWeekStart(date);
  const end = new Date(start);
  end.setDate(end.getDate() + 6);
  end.setHours(23, 59, 59, 999);
  return end;
}

export function getWeekDates(startDate: Date): Date[] {
  const dates: Date[] = [];
  const start = getWeekStart(startDate);
  for (let i = 0; i < 7; i++) {
    const date = new Date(start);
    date.setDate(date.getDate() + i);
    dates.push(date);
  }
  return dates;
}

export function formatDateParam(date: Date): string {
  return date.toISOString().split("T")[0];
}

export function parseWeekParam(param: string | null): Date {
  if (!param) return new Date();
  const parsed = new Date(param);
  return isNaN(parsed.getTime()) ? new Date() : parsed;
}

// State utilities
export function getStateName(stateCode: string): string {
  const states: Record<string, string> = {
    AL: "Alabama",
    AK: "Alaska",
    AZ: "Arizona",
    AR: "Arkansas",
    CA: "California",
    CO: "Colorado",
    CT: "Connecticut",
    DE: "Delaware",
    FL: "Florida",
    GA: "Georgia",
    HI: "Hawaii",
    ID: "Idaho",
    IL: "Illinois",
    IN: "Indiana",
    IA: "Iowa",
    KS: "Kansas",
    KY: "Kentucky",
    LA: "Louisiana",
    ME: "Maine",
    MD: "Maryland",
    MA: "Massachusetts",
    MI: "Michigan",
    MN: "Minnesota",
    MS: "Mississippi",
    MO: "Missouri",
    MT: "Montana",
    NE: "Nebraska",
    NV: "Nevada",
    NH: "New Hampshire",
    NJ: "New Jersey",
    NM: "New Mexico",
    NY: "New York",
    NC: "North Carolina",
    ND: "North Dakota",
    OH: "Ohio",
    OK: "Oklahoma",
    OR: "Oregon",
    PA: "Pennsylvania",
    RI: "Rhode Island",
    SC: "South Carolina",
    SD: "South Dakota",
    TN: "Tennessee",
    TX: "Texas",
    UT: "Utah",
    VT: "Vermont",
    VA: "Virginia",
    WA: "Washington",
    WV: "West Virginia",
    WI: "Wisconsin",
    WY: "Wyoming",
    DC: "District of Columbia",
    PR: "Puerto Rico",
    GU: "Guam",
    VI: "U.S. Virgin Islands",
    AS: "American Samoa",
    MP: "Northern Mariana Islands",
  };
  return states[stateCode] || stateCode;
}

// Member district display
export function getMemberLocation(
  state: string,
  district: number | null,
  chamber: string
): string {
  if (chamber === "senate") {
    return getStateName(state);
  }
  if (district === 0) {
    return `${getStateName(state)} (At-Large)`;
  }
  return `${getStateName(state)}, District ${district}`;
}

// Bill type utilities
export function getBillTypeLabel(billType: string): string {
  const types: Record<string, string> = {
    hr: "H.R.",
    s: "S.",
    hjres: "H.J.Res.",
    sjres: "S.J.Res.",
    hconres: "H.Con.Res.",
    sconres: "S.Con.Res.",
    hres: "H.Res.",
    sres: "S.Res.",
  };
  return types[billType] || billType.toUpperCase();
}

// Truncate text
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + "...";
}
