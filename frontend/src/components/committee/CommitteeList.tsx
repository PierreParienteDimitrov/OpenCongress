"use client";

import { useInfiniteQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import CommitteeCard from "@/components/committee/CommitteeCard";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getCommitteesPaginated } from "@/lib/api";
import type { CommitteeListItem, PaginatedResponse } from "@/types";

interface CommitteeListProps {
  initialData: PaginatedResponse<CommitteeListItem>;
}

function CommitteeCardSkeleton() {
  return (
    <Card className="h-full py-4">
      <div className="space-y-3 px-6">
        <div className="flex items-start justify-between">
          <Skeleton className="h-4 w-48 bg-secondary" />
          <Skeleton className="h-5 w-14 bg-secondary" />
        </div>
        <Skeleton className="h-3 w-36 bg-secondary" />
        <Skeleton className="h-3 w-32 bg-secondary" />
        <div className="flex gap-4">
          <Skeleton className="h-3 w-20 bg-secondary" />
          <Skeleton className="h-3 w-16 bg-secondary" />
        </div>
      </div>
    </Card>
  );
}

export default function CommitteeList({ initialData }: CommitteeListProps) {
  const loadMoreRef = useRef<HTMLDivElement>(null);
  const [searchInput, setSearchInput] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [chamberFilter, setChamberFilter] = useState("");

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchInput);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const isFiltering = debouncedSearch.length > 0 || chamberFilter.length > 0;

  const { data, fetchNextPage, hasNextPage, isFetchingNextPage, status } =
    useInfiniteQuery({
      queryKey: ["committees", debouncedSearch, chamberFilter],
      queryFn: async ({ pageParam }) =>
        getCommitteesPaginated(pageParam, debouncedSearch, chamberFilter),
      initialPageParam: 1,
      getNextPageParam: (lastPage) =>
        lastPage.next
          ? Number(new URL(lastPage.next).searchParams.get("page"))
          : undefined,
      initialData: isFiltering
        ? undefined
        : { pages: [initialData], pageParams: [1] },
    });

  // Intersection observer for auto-loading
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
          fetchNextPage();
        }
      },
      { threshold: 0.1 }
    );

    if (loadMoreRef.current) observer.observe(loadMoreRef.current);
    return () => observer.disconnect();
  }, [fetchNextPage, hasNextPage, isFetchingNextPage]);

  const allCommittees =
    data?.pages.flatMap((page) => page.results) ?? [];

  return (
    <div>
      {/* Filters */}
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search committees..."
            className="h-10 w-full rounded-md border border-input bg-card pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>

        {/* Chamber filter */}
        <div className="flex gap-2">
          {[
            { label: "All", value: "" },
            { label: "Senate", value: "senate" },
            { label: "House", value: "house" },
          ].map((option) => (
            <button
              key={option.value}
              onClick={() => setChamberFilter(option.value)}
              className={`cursor-pointer rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                chamberFilter === option.value
                  ? "bg-primary text-primary-foreground"
                  : "bg-card text-muted-foreground hover:bg-accent"
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* Results count */}
      {data && (
        <p className="mb-4 text-sm text-muted-foreground">
          {data.pages[0].count} committee
          {data.pages[0].count !== 1 ? "s" : ""}
        </p>
      )}

      {/* Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {allCommittees.map((committee) => (
          <CommitteeCard
            key={committee.committee_id}
            committee={committee}
          />
        ))}
        {isFetchingNextPage &&
          Array.from({ length: 3 }).map((_, i) => (
            <CommitteeCardSkeleton key={`skeleton-next-${i}`} />
          ))}
      </div>

      {/* Empty state */}
      {status === "success" && allCommittees.length === 0 && (
        <p className="py-12 text-center text-sm text-muted-foreground">
          No committees found.
        </p>
      )}

      {/* Load more trigger */}
      <div ref={loadMoreRef} className="mt-8 flex justify-center py-4" />
    </div>
  );
}
