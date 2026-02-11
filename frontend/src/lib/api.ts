/**
 * API client for fetching data from the backend.
 * Designed for use with Next.js Server Components.
 */

import type {
  BillCalendarItem,
  BillDetail,
  BillListItem,
  MemberDetail,
  MemberListItem,
  PaginatedResponse,
  VoteCalendarItem,
  VoteSummary,
  WeeklySummary,
  WeeklySummaryListItem,
} from "@/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface FetchOptions {
  next?: {
    revalidate?: number;
    tags?: string[];
  };
}

class APIError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "APIError";
    this.status = status;
  }
}

async function fetchAPI<T>(
  endpoint: string,
  options: FetchOptions = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
      },
      ...options,
    });

    if (!response.ok) {
      throw new APIError(
        `API request failed: ${response.statusText}`,
        response.status
      );
    }

    return response.json();
  } catch (error) {
    // During build time (no backend available), return empty defaults
    // so pages can pre-render with fallback state and revalidate at runtime
    if (error instanceof APIError) {
      throw error;
    }
    console.warn(
      `[API] Backend unreachable for ${endpoint}, returning empty default`
    );
    return { count: 0, next: null, previous: null, results: [] } as unknown as T;
  }
}

// Member endpoints
export async function getMembers(
  params: Record<string, string> = {}
): Promise<PaginatedResponse<MemberListItem>> {
  const searchParams = new URLSearchParams(params);
  const query = searchParams.toString();
  return fetchAPI<PaginatedResponse<MemberListItem>>(
    `/members/${query ? `?${query}` : ""}`,
    { next: { revalidate: 3600 } }
  );
}

export async function getMember(bioguideId: string): Promise<MemberDetail> {
  return fetchAPI<MemberDetail>(`/members/${bioguideId}/`, {
    next: { revalidate: 3600 },
  });
}

export async function getRepresentatives(
  params: Record<string, string> = {}
): Promise<PaginatedResponse<MemberListItem>> {
  const searchParams = new URLSearchParams(params);
  const query = searchParams.toString();
  return fetchAPI<PaginatedResponse<MemberListItem>>(
    `/members/representatives/${query ? `?${query}` : ""}`,
    { next: { revalidate: 86400 } }
  );
}

export async function getSenators(
  params: Record<string, string> = {}
): Promise<PaginatedResponse<MemberListItem>> {
  const searchParams = new URLSearchParams(params);
  const query = searchParams.toString();
  return fetchAPI<PaginatedResponse<MemberListItem>>(
    `/members/senators/${query ? `?${query}` : ""}`,
    { next: { revalidate: 3600 } }
  );
}

// Bill endpoints
export async function getBills(
  params: Record<string, string> = {}
): Promise<PaginatedResponse<BillListItem>> {
  const searchParams = new URLSearchParams(params);
  const query = searchParams.toString();
  return fetchAPI<PaginatedResponse<BillListItem>>(
    `/bills/${query ? `?${query}` : ""}`
  );
}

export async function getBill(billId: string): Promise<BillDetail> {
  return fetchAPI<BillDetail>(`/bills/${billId}/`, {
    next: { revalidate: 86400 },
  });
}

export async function getBillsCalendar(
  dateFrom: string,
  dateTo: string
): Promise<PaginatedResponse<BillCalendarItem>> {
  return fetchAPI<PaginatedResponse<BillCalendarItem>>(
    `/bills/calendar/?date_from=${dateFrom}&date_to=${dateTo}`,
    { next: { revalidate: 300 } }
  );
}

// Vote endpoints
export async function getVotes(
  params: Record<string, string> = {}
): Promise<PaginatedResponse<VoteSummary>> {
  const searchParams = new URLSearchParams(params);
  const query = searchParams.toString();
  return fetchAPI<PaginatedResponse<VoteSummary>>(
    `/votes/${query ? `?${query}` : ""}`
  );
}

export async function getVote(voteId: string): Promise<VoteSummary> {
  return fetchAPI<VoteSummary>(`/votes/${voteId}/`, {
    next: { revalidate: 86400 },
  });
}

export async function getVotesCalendar(
  dateFrom: string,
  dateTo: string
): Promise<PaginatedResponse<VoteCalendarItem>> {
  return fetchAPI<PaginatedResponse<VoteCalendarItem>>(
    `/votes/calendar/?date_from=${dateFrom}&date_to=${dateTo}`,
    { next: { revalidate: 300 } }
  );
}

// Weekly summary endpoints
export async function getCurrentWeeklySummaries(): Promise<WeeklySummary[]> {
  return fetchAPI<WeeklySummary[]>("/content/weekly-summaries/current/", {
    next: { revalidate: 900 }, // 15 minutes
  });
}

export async function getWeeklySummaryByWeek(
  year: number,
  week: number
): Promise<WeeklySummary[]> {
  return fetchAPI<WeeklySummary[]>(
    `/content/weekly-summaries/week/${year}/${week}/`,
    { next: { revalidate: 86400 } } // 24 hours
  );
}

export async function getWeeklySummaries(): Promise<
  PaginatedResponse<WeeklySummaryListItem>
> {
  return fetchAPI<PaginatedResponse<WeeklySummaryListItem>>(
    "/content/weekly-summaries/",
    { next: { revalidate: 900 } }
  );
}

// Client-side pagination functions for infinite scroll
// These are designed to be called from React Query on the client side

const BROWSER_API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchAPIClient<T>(endpoint: string): Promise<T> {
  const url = `${BROWSER_API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new APIError(
      `API request failed: ${response.statusText}`,
      response.status
    );
  }

  return response.json();
}

export async function getSenatorsPaginated(
  page: number = 1
): Promise<PaginatedResponse<MemberListItem>> {
  return fetchAPIClient<PaginatedResponse<MemberListItem>>(
    `/members/senators/?page=${page}&ordering=last_name`
  );
}

export async function getRepresentativesPaginated(
  page: number = 1
): Promise<PaginatedResponse<MemberListItem>> {
  return fetchAPIClient<PaginatedResponse<MemberListItem>>(
    `/members/representatives/?page=${page}&ordering=last_name`
  );
}

export { APIError };
