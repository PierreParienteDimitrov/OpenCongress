/**
 * Authenticated API client for client-side requests.
 * Uses the NextAuth session to attach JWT tokens.
 */

import { getSession } from "next-auth/react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

class APIError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "APIError";
    this.status = status;
  }
}

async function fetchAuthenticated<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const session = await getSession();

  if (!session?.djangoAccessToken) {
    throw new APIError("Not authenticated", 401);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${session.djangoAccessToken}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const text = await response.text();
    throw new APIError(text || response.statusText, response.status);
  }

  // 204 No Content
  if (response.status === 204) {
    return undefined as unknown as T;
  }

  return response.json();
}

// ── API Key management ──

export interface ConfiguredAPIKey {
  id: number;
  provider: string;
  provider_display: string;
  created_at: string;
  updated_at: string;
}

export async function fetchAPIKeys(): Promise<ConfiguredAPIKey[]> {
  return fetchAuthenticated<ConfiguredAPIKey[]>("/auth/api-keys/");
}

export async function createAPIKey(
  provider: string,
  apiKey: string,
): Promise<{ provider: string; created: boolean }> {
  return fetchAuthenticated("/auth/api-keys/create/", {
    method: "POST",
    body: JSON.stringify({ provider, api_key: apiKey }),
  });
}

export async function deleteAPIKey(provider: string): Promise<void> {
  return fetchAuthenticated(`/auth/api-keys/${provider}/delete/`, {
    method: "DELETE",
  });
}

// ── My Representatives / Follows ──

import type { MemberListItem, RepActivityResponse } from "@/types";

export interface MyRepresentativesResponse {
  followed_ids: string[];
  followed_members: MemberListItem[];
}

export async function fetchMyRepresentatives(): Promise<MyRepresentativesResponse> {
  return fetchAuthenticated<MyRepresentativesResponse>(
    "/auth/my-representatives/",
  );
}

export async function fetchRepActivity(): Promise<RepActivityResponse> {
  return fetchAuthenticated<RepActivityResponse>(
    "/auth/my-representatives/activity/",
  );
}

export async function followMember(
  bioguideId: string,
): Promise<{ bioguide_id: string; followed: boolean }> {
  return fetchAuthenticated(`/auth/follow/${bioguideId}/`, {
    method: "POST",
  });
}

export async function unfollowMember(bioguideId: string): Promise<void> {
  return fetchAuthenticated(`/auth/follow/${bioguideId}/`, {
    method: "DELETE",
  });
}

// ── Chat streaming ──

export interface ChatStreamOptions {
  provider: string;
  model?: string;
  messages: { role: "user" | "assistant"; content: string }[];
  pageContext: { type: string; data: Record<string, unknown> };
  onChunk: (text: string) => void;
  onDone: () => void;
  onError: (error: string) => void;
}

export async function streamChat({
  provider,
  model,
  messages,
  pageContext,
  onChunk,
  onDone,
  onError,
}: ChatStreamOptions): Promise<void> {
  const session = await getSession();
  if (!session?.djangoAccessToken) {
    onError("Not authenticated");
    return;
  }

  const response = await fetch(`${API_BASE_URL}/auth/chat/stream/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${session.djangoAccessToken}`,
    },
    body: JSON.stringify({
      provider,
      model,
      messages,
      page_context: pageContext,
    }),
  });

  if (!response.body) {
    onError("No response body");
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const text = decoder.decode(value);
      const lines = text.split("\n");

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        try {
          const data = JSON.parse(line.slice(6));
          if (data.chunk) {
            onChunk(data.chunk);
          } else if (data.done) {
            onDone();
          } else if (data.error) {
            onError(data.error);
          }
        } catch {
          // Ignore malformed SSE lines
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export { APIError };
