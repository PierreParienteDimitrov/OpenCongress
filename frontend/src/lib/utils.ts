/**
 * Utility functions for formatting and display.
 */

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

import type { BillCalendarItem, VoteCalendarItem, VotePosition, VoteResult } from "@/types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

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
    D: "oklch(0.45 0.11 256)", // Old Glory Blue 500
    R: "oklch(0.498 0.185 14)", // Old Glory Red 500
    I: "#7c3aed", // violet-600
  };
  return colors[party] || "#6b7280"; // gray-500
}

export function getPartyBgColor(party: string): string {
  const colors: Record<string, string> = {
    D: "bg-glory-blue-100 text-glory-blue-800",
    R: "bg-glory-red-100 text-glory-red-800",
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
    nay: "text-glory-red-500",
    present: "text-yellow-600",
    not_voting: "text-gray-400",
  };
  return colors[position] || "text-gray-600";
}

export function getPositionBgColor(position: VotePosition): string {
  const colors: Record<VotePosition, string> = {
    yea: "bg-green-600/30 text-green-100",
    nay: "bg-glory-red-500/30 text-glory-red-100",
    present: "bg-yellow-600/30 text-yellow-100",
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
    failed: "text-glory-red-500",
    agreed: "text-green-600",
    rejected: "text-glory-red-500",
  };
  return colors[result] || "text-gray-600";
}

export function getResultBgColor(result: VoteResult): string {
  const colors: Record<VoteResult, string> = {
    passed: "bg-green-600/30 text-green-100",
    failed: "bg-glory-red-500/30 text-glory-red-100",
    agreed: "bg-green-600/30 text-green-100",
    rejected: "bg-glory-red-500/30 text-glory-red-100",
  };
  return colors[result] || "bg-gray-100 text-gray-800";
}

// Date utilities
// Parse a "YYYY-MM-DD" string as local time (not UTC) to avoid off-by-one day errors.
function parseDateLocal(dateString: string): Date {
  const [year, month, day] = dateString.split("-").map(Number);
  return new Date(year, month - 1, day);
}

export function formatDate(dateString: string | null): string {
  if (!dateString) return "";
  const date = parseDateLocal(dateString);
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatDateLong(dateString: string | null): string {
  if (!dateString) return "";
  const date = parseDateLocal(dateString);
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
  const parsed = parseDateLocal(param);
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

// ISO week number (matches Python's isocalendar())
export function getISOWeekNumber(date: Date): { year: number; week: number } {
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  // Thursday of current week determines the year
  d.setDate(d.getDate() + 3 - ((d.getDay() + 6) % 7));
  const yearStart = new Date(d.getFullYear(), 0, 1);
  const week = Math.ceil(
    ((d.getTime() - yearStart.getTime()) / 86400000 + 1) / 7
  );
  return { year: d.getFullYear(), week };
}

// Get the Monday of a given ISO week
export function getDateFromISOWeek(year: number, week: number): Date {
  const jan4 = new Date(year, 0, 4);
  const dayOfWeek = jan4.getDay() || 7; // Monday=1 ... Sunday=7
  const monday = new Date(jan4);
  monday.setDate(jan4.getDate() - dayOfWeek + 1 + (week - 1) * 7);
  return monday;
}

// Truncate text
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + "...";
}

// Relative time formatting
export function formatRelativeTime(dateString: string): string {
  if (!dateString) return "";
  const now = new Date();
  const date = new Date(dateString + "T12:00:00"); // noon to avoid timezone issues
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "1d ago";
  if (diffDays < 7) return `${diffDays}d ago`;
  if (diffDays < 14) return "1 week ago";
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  return formatDate(dateString);
}

// News-style vote headline: "Senate Passes Defense Bill 62-38"
export function generateVoteHeadline(vote: VoteCalendarItem): string {
  const chamber = getChamberShortName(vote.chamber);
  const resultVerb: Record<string, string> = {
    passed: "Passes",
    failed: "Rejects",
    agreed: "Agrees To",
    rejected: "Rejects",
  };
  const verb = resultVerb[vote.result] || "Votes On";
  const tally = `${vote.total_yea}-${vote.total_nay}`;

  // Prefer bill title for a readable headline
  if (vote.bill_short_title) {
    return `${chamber} ${verb} ${truncate(vote.bill_short_title, 60)} ${tally}`;
  }
  // If we have a bill number but no title, use that
  if (vote.bill_display_number) {
    return `${chamber} ${verb} ${vote.bill_display_number} (${vote.description}) ${tally}`;
  }
  // Fallback: use question/description directly without verb to avoid "Passes On Passage"
  return `${chamber}: ${truncate(vote.description, 60)} — ${tally}`;
}

// News-style bill headline: "H.R. 1234: Referred to Committee"
export function generateBillHeadline(bill: BillCalendarItem): string {
  const title = bill.short_title || bill.latest_action_text;
  return `${bill.display_number}: ${truncate(title, 70)}`;
}
