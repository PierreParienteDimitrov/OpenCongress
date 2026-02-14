"use client";

import { useInfiniteQuery } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { Search } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

import type { MemberListItem, PaginatedResponse } from "@/types";
import {
  cn,
  getPartyBgColor,
  getPartyName,
  getMemberLocation,
} from "@/lib/utils";
import { getMemberRoute } from "@/lib/routes";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";

interface MemberListProps {
  chamber: "senate" | "house";
  initialData: PaginatedResponse<MemberListItem>;
  fetchFn: (page: number, search: string) => Promise<PaginatedResponse<MemberListItem>>;
}

function MemberCard({ member, chamber }: { member: MemberListItem; chamber: "senate" | "house" }) {
  return (
    <Link href={getMemberRoute(member.bioguide_id, chamber)}>
      <div className="group flex flex-row items-center gap-4 border-b border-border p-4 transition-colors hover:bg-secondary/50">
        {/* Photo */}
        <div className="shrink-0">
          {member.photo_url ? (
            <Image
              src={member.photo_url}
              alt={member.full_name}
              width={64}
              height={64}
              className="h-16 w-16 rounded-full object-cover"
            />
          ) : (
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-secondary">
              <span className="text-lg font-medium text-muted-foreground">
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
          <h3 className="truncate font-semibold text-foreground group-hover:text-accent">
            {member.full_name}
          </h3>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            <Badge className={cn(getPartyBgColor(member.party))}>
              {getPartyName(member.party)}
            </Badge>
            <span className="text-sm text-muted-foreground">
              {getMemberLocation(member.state, member.district, member.chamber)}
            </span>
          </div>
        </div>

        {/* Arrow */}
        <svg
          className="h-5 w-5 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-1 group-hover:text-foreground"
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
      </div>
    </Link>
  );
}

function MemberCardSkeleton() {
  return (
    <div className="flex flex-row items-center gap-4 border-b border-border p-4">
      <Skeleton className="h-16 w-16 shrink-0 rounded-full bg-secondary" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-5 w-40 bg-secondary" />
        <div className="flex gap-2">
          <Skeleton className="h-5 w-20 rounded-full bg-secondary" />
          <Skeleton className="h-5 w-32 bg-secondary" />
        </div>
      </div>
    </div>
  );
}

export default function MemberList({ chamber, initialData, fetchFn }: MemberListProps) {
  const loadMoreRef = useRef<HTMLDivElement>(null);
  const [searchInput, setSearchInput] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  // Debounce search input by 300ms
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchInput);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const isSearching = debouncedSearch.length > 0;

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isFetching,
    status,
  } = useInfiniteQuery({
    queryKey: ["members", chamber, debouncedSearch],
    queryFn: async ({ pageParam }) => {
      return fetchFn(pageParam, debouncedSearch);
    },
    initialPageParam: 1,
    getNextPageParam: (lastPage, allPages) => {
      return lastPage.next ? allPages.length + 1 : undefined;
    },
    ...(isSearching
      ? {}
      : {
          initialData: {
            pages: [initialData],
            pageParams: [1],
          },
        }),
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
      {/* Search */}
      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          placeholder="Search by name or state..."
          className="h-10 w-full rounded-md border border-input bg-card pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-2 focus:ring-ring/50"
        />
      </div>

      {/* Count */}
      <p className="mb-4 text-sm text-muted-foreground">
        {isFetching && !isFetchingNextPage
          ? "Searching..."
          : `Showing ${allMembers.length} of ${totalCount} members`}
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
          <Button variant="secondary" onClick={() => fetchNextPage()}>
            Load More
          </Button>
        )}
        {!hasNextPage && allMembers.length > 0 && (
          <p className="text-sm text-muted-foreground">
            All members loaded
          </p>
        )}
      </div>
    </div>
  );
}
