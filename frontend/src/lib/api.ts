/**
 * API client for fetching data from the backend.
 * Designed for use with Next.js Server Components.
 */

import * as Sentry from "@sentry/nextjs";
import type {
  BillCalendarItem,
  BillDetail,
  BillListItem,
  MemberDetail,
  MemberListItem,
  PaginatedResponse,
  Seat,
  SeatWithVote,
  VoteCalendarItem,
  VoteSummary,
  WeeklySummary,
  WeeklySummaryListItem,
  ZipLookupResult,
} from "@/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface FetchOptions {
  next?: {
    revalidate?: number;
    tags?: string[];
  };
  cache?: RequestCache;
}

const isDev = process.env.NODE_ENV === "development";

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
    const fetchOptions: RequestInit = {
      headers: {
        "Content-Type": "application/json",
      },
      ...(isDev ? { cache: "no-store" as const } : options),
    };
    const response = await fetch(url, fetchOptions);

    if (!response.ok) {
      throw new APIError(
        `API request failed: ${response.statusText}`,
        response.status
      );
    }

    return response.json();
  } catch (error) {
    // Re-throw API errors (4xx/5xx) so callers can handle them
    // (e.g. detail pages calling notFound() on 404)
    if (error instanceof APIError) {
      throw error;
    }

    // During build/prerendering, network errors return empty defaults so
    // pages render with fallback state and revalidate with real data at runtime
    Sentry.captureException(error, {
      tags: { source: "api", endpoint },
    });
    console.warn(
      `[API] Request failed for ${endpoint}: ${error instanceof Error ? error.message : error}`
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

// Seat endpoints
export async function getSeats(
  chamber: "house" | "senate"
): Promise<Seat[]> {
  const data = await fetchAPI<Seat[]>(`/seats/?chamber=${chamber}`, {
    next: { revalidate: 86400 },
  });
  return Array.isArray(data) ? data : [];
}

export async function getSeatVoteOverlay(
  chamber: "house" | "senate",
  voteId: string
): Promise<SeatWithVote[]> {
  const data = await fetchAPI<SeatWithVote[]>(
    `/seats/vote-overlay/?chamber=${chamber}&vote_id=${encodeURIComponent(voteId)}`,
    { next: { revalidate: 86400 } }
  );
  return Array.isArray(data) ? data : [];
}

// Weekly summary endpoints
export async function getCurrentWeeklySummaries(): Promise<WeeklySummary[]> {
  const data = await fetchAPI<WeeklySummary[]>(
    "/content/weekly-summaries/current/",
    {
      next: { revalidate: 900 }, // 15 minutes
    }
  );
  // fetchAPI fallback returns a paginated object on failure; ensure we return an array
  return Array.isArray(data) ? data : [];
}

export async function getWeeklySummaryByWeek(
  year: number,
  week: number
): Promise<WeeklySummary[]> {
  const data = await fetchAPI<WeeklySummary[]>(
    `/content/weekly-summaries/week/${year}/${week}/`,
    { next: { revalidate: 86400 } } // 24 hours
  );
  // fetchAPI fallback returns a paginated object on failure; ensure we return an array
  return Array.isArray(data) ? data : [];
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
  page: number = 1,
  search: string = ""
): Promise<PaginatedResponse<MemberListItem>> {
  const params = new URLSearchParams({ page: String(page), ordering: "last_name" });
  if (search) params.set("search", search);
  return fetchAPIClient<PaginatedResponse<MemberListItem>>(
    `/members/senators/?${params}`
  );
}

export async function getRepresentativesPaginated(
  page: number = 1,
  search: string = ""
): Promise<PaginatedResponse<MemberListItem>> {
  const params = new URLSearchParams({ page: String(page), ordering: "last_name" });
  if (search) params.set("search", search);
  return fetchAPIClient<PaginatedResponse<MemberListItem>>(
    `/members/representatives/?${params}`
  );
}

export async function getSeatVoteOverlayClient(
  chamber: "house" | "senate",
  voteId: string
): Promise<SeatWithVote[]> {
  return fetchAPIClient<SeatWithVote[]>(
    `/seats/vote-overlay/?chamber=${chamber}&vote_id=${encodeURIComponent(voteId)}`
  );
}

// Unpaginated member fetches for map views
export async function getAllSenators(): Promise<MemberListItem[]> {
  const data = await fetchAPI<PaginatedResponse<MemberListItem>>(
    "/members/senators/?page_size=500&ordering=last_name",
    { next: { revalidate: 3600 } }
  );
  return data.results ?? [];
}

export async function getAllRepresentatives(): Promise<MemberListItem[]> {
  const data = await fetchAPI<PaginatedResponse<MemberListItem>>(
    "/members/representatives/?page_size=500&ordering=last_name",
    { next: { revalidate: 3600 } }
  );
  return data.results ?? [];
}

// Zip code lookup (client-side)
export async function lookupZipCode(zip: string): Promise<ZipLookupResult> {
  return fetchAPIClient<ZipLookupResult>(
    `/members/zip-lookup/?zip=${encodeURIComponent(zip)}`
  );
}

export { APIError };
