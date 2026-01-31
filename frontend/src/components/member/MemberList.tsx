"use client";

import { useInfiniteQuery } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import Link from "next/link";

import type { MemberListItem, PaginatedResponse } from "@/types";
import {
  getPartyBgColor,
  getPartyName,
  getMemberLocation,
} from "@/lib/utils";
import { getMemberRoute } from "@/lib/routes";

interface MemberListProps {
  chamber: "senate" | "house";
  initialData: PaginatedResponse<MemberListItem>;
  fetchFn: (page: number) => Promise<PaginatedResponse<MemberListItem>>;
}

function MemberCard({ member, chamber }: { member: MemberListItem; chamber: "senate" | "house" }) {
  return (
    <Link
      href={getMemberRoute(member.bioguide_id, chamber)}
      className="group flex items-center gap-4 rounded-lg border border-zinc-200 bg-white p-4 transition-all hover:border-zinc-300 hover:shadow-md dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-700"
    >
      {/* Photo */}
      <div className="shrink-0">
        {member.photo_url ? (
          <img
            src={member.photo_url}
            alt={member.full_name}
            className="h-16 w-16 rounded-full object-cover"
            loading="lazy"
          />
        ) : (
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-zinc-200 dark:bg-zinc-700">
            <span className="text-lg font-medium text-zinc-500 dark:text-zinc-400">
              {member.full_name
                .split(" ")
                .map((n) => n[0])
                .join("")
                .slice(0, 2)}
            </span>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="min-w-0 flex-1">
        <h3 className="truncate font-semibold text-zinc-900 group-hover:text-blue-600 dark:text-zinc-50 dark:group-hover:text-blue-400">
          {member.full_name}
        </h3>
        <div className="mt-1 flex flex-wrap items-center gap-2">
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${getPartyBgColor(member.party)}`}
          >
            {getPartyName(member.party)}
          </span>
          <span className="text-sm text-zinc-500 dark:text-zinc-400">
            {getMemberLocation(member.state, member.district, member.chamber)}
          </span>
        </div>
      </div>

      {/* Arrow */}
      <svg
        className="h-5 w-5 shrink-0 text-zinc-400 transition-transform group-hover:translate-x-1 group-hover:text-zinc-600 dark:text-zinc-500 dark:group-hover:text-zinc-300"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 5l7 7-7 7"
        />
      </svg>
    </Link>
  );
}

function MemberCardSkeleton() {
  return (
    <div className="flex items-center gap-4 rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
      <div className="h-16 w-16 shrink-0 animate-pulse rounded-full bg-zinc-200 dark:bg-zinc-700" />
      <div className="flex-1 space-y-2">
        <div className="h-5 w-40 animate-pulse rounded bg-zinc-200 dark:bg-zinc-700" />
        <div className="flex gap-2">
          <div className="h-5 w-20 animate-pulse rounded-full bg-zinc-200 dark:bg-zinc-700" />
          <div className="h-5 w-32 animate-pulse rounded bg-zinc-200 dark:bg-zinc-700" />
        </div>
      </div>
    </div>
  );
}

export default function MemberList({ chamber, initialData, fetchFn }: MemberListProps) {
  const loadMoreRef = useRef<HTMLDivElement>(null);

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    status,
  } = useInfiniteQuery({
    queryKey: ["members", chamber],
    queryFn: async ({ pageParam }) => {
      return fetchFn(pageParam);
    },
    initialPageParam: 1,
    getNextPageParam: (lastPage, allPages) => {
      return lastPage.next ? allPages.length + 1 : undefined;
    },
    initialData: {
      pages: [initialData],
      pageParams: [1],
    },
  });

  // Intersection Observer for infinite scroll
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
          fetchNextPage();
        }
      },
      { threshold: 0.1 }
    );

    if (loadMoreRef.current) {
      observer.observe(loadMoreRef.current);
    }

    return () => observer.disconnect();
  }, [fetchNextPage, hasNextPage, isFetchingNextPage]);

  const allMembers = data?.pages.flatMap((page) => page.results) ?? [];
  const totalCount = data?.pages[0]?.count ?? 0;

  if (status === "error") {
    return (
      <div className="py-12 text-center">
        <p className="text-red-600 dark:text-red-400">
          Failed to load members. Please try again later.
        </p>
      </div>
    );
  }

  return (
    <div>
      {/* Count */}
      <p className="mb-4 text-sm text-zinc-500 dark:text-zinc-400">
        Showing {allMembers.length} of {totalCount} members
      </p>

      {/* Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {allMembers.map((member) => (
          <MemberCard key={member.bioguide_id} member={member} chamber={chamber} />
        ))}

        {/* Loading skeletons */}
        {isFetchingNextPage &&
          Array.from({ length: 6 }).map((_, i) => (
            <MemberCardSkeleton key={`skeleton-${i}`} />
          ))}
      </div>

      {/* Load more trigger */}
      <div ref={loadMoreRef} className="mt-8 flex justify-center py-4">
        {hasNextPage && !isFetchingNextPage && (
          <button
            onClick={() => fetchNextPage()}
            className="rounded-lg bg-zinc-100 px-6 py-2 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700"
          >
            Load More
          </button>
        )}
        {!hasNextPage && allMembers.length > 0 && (
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            All members loaded
          </p>
        )}
      </div>
    </div>
  );
}
