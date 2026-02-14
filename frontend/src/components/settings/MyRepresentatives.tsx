"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { MapPin, Loader2, Search, UserPlus, UserMinus } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import {
  fetchMyRepresentatives,
  followMember,
  unfollowMember,
} from "@/lib/api-client";
import { lookupZipCode } from "@/lib/api";
import { cn, getPartyBgColor, getPartyName } from "@/lib/utils";
import { getMemberRoute } from "@/lib/routes";
import type { ZipLookupResult, MemberListItem } from "@/types";

function RepCard({
  member,
  isFollowed,
  onFollow,
  onUnfollow,
  isPending,
}: {
  member: MemberListItem;
  isFollowed: boolean;
  onFollow: () => void;
  onUnfollow: () => void;
  isPending: boolean;
}) {
  return (
    <div className="flex items-center gap-3 rounded border border-border bg-card p-3">
      <Link
        href={getMemberRoute(member.bioguide_id, member.chamber, member.full_name)}
        className="flex flex-1 items-center gap-3 cursor-pointer min-w-0"
      >
        <Image
          src={member.photo_url}
          alt={member.full_name}
          width={40}
          height={40}
          className="h-10 w-10 rounded-full object-cover"
        />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold text-foreground">
            {member.full_name}
          </p>
          <div className="mt-1 flex items-center gap-2">
            <Badge className={cn("text-xs", getPartyBgColor(member.party))}>
              {getPartyName(member.party)}
            </Badge>
            <span className="text-xs text-muted-foreground">
              {member.chamber === "senate" ? "Senator" : "Representative"}
            </span>
          </div>
        </div>
      </Link>
      <Button
        variant={isFollowed ? "outline" : "default"}
        size="sm"
        onClick={isFollowed ? onUnfollow : onFollow}
        disabled={isPending}
        className="shrink-0 cursor-pointer"
      >
        {isPending ? (
          <Loader2 className="mr-1.5 size-3.5 animate-spin" />
        ) : isFollowed ? (
          <UserMinus className="mr-1.5 size-3.5" />
        ) : (
          <UserPlus className="mr-1.5 size-3.5" />
        )}
        {isFollowed ? "Following" : "Follow"}
      </Button>
    </div>
  );
}

export function MyRepresentatives() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["my-representatives"],
    queryFn: fetchMyRepresentatives,
  });

  const followedIds = new Set(data?.followed_ids ?? []);

  const followMut = useMutation({
    mutationFn: followMember,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-representatives"] });
    },
  });

  const unfollowMut = useMutation({
    mutationFn: unfollowMember,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-representatives"] });
    },
  });

  // Track which member is being toggled to show spinner on the right button
  const [pendingId, setPendingId] = useState<string | null>(null);

  async function handleFollow(bioguideId: string) {
    setPendingId(bioguideId);
    try {
      await followMut.mutateAsync(bioguideId);
    } finally {
      setPendingId(null);
    }
  }

  async function handleUnfollow(bioguideId: string) {
    setPendingId(bioguideId);
    try {
      await unfollowMut.mutateAsync(bioguideId);
    } finally {
      setPendingId(null);
    }
  }

  // Search state
  const [zip, setZip] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchResult, setSearchResult] = useState<ZipLookupResult | null>(
    null,
  );

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = zip.trim();
    if (!trimmed) return;

    if (!/^\d{5}$/.test(trimmed)) {
      setSearchError("Please enter a valid 5-digit zip code");
      return;
    }

    setSearching(true);
    setSearchError(null);

    try {
      const result = await lookupZipCode(trimmed);
      setSearchResult(result);
    } catch {
      setSearchError(
        "Could not find a congressional district for this zip code",
      );
    } finally {
      setSearching(false);
    }
  }

  function handleClear() {
    setZip("");
    setSearchError(null);
    setSearchResult(null);
  }

  if (isLoading) {
    return (
      <Card className="py-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="size-5" />
            My Representatives
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Loading...
          </div>
        </CardContent>
      </Card>
    );
  }

  const hasFollowed = data && data.followed_members.length > 0;

  return (
    <Card className="py-4">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MapPin className="size-5" />
          My Representatives
        </CardTitle>
        <CardDescription>
          Find your congressional representatives by zip code and follow them to
          get a personalized feed and notifications.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Followed members */}
        {hasFollowed && (
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-foreground">Following</h3>
            <div className="space-y-2">
              {data.followed_members.map((member) => (
                <RepCard
                  key={member.bioguide_id}
                  member={member}
                  isFollowed={true}
                  onFollow={() => handleFollow(member.bioguide_id)}
                  onUnfollow={() => handleUnfollow(member.bioguide_id)}
                  isPending={pendingId === member.bioguide_id}
                />
              ))}
            </div>
          </div>
        )}

        {hasFollowed && <Separator />}

        {/* Zip code search */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-foreground">
            Find Representatives
          </h3>
          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                value={zip}
                onChange={(e) => setZip(e.target.value)}
                placeholder="Search by zip code..."
                maxLength={5}
                className="h-10 w-full rounded-md border border-input bg-card pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-2 focus:ring-ring/50"
              />
            </div>
            <button
              type="submit"
              disabled={searching}
              className="inline-flex h-10 cursor-pointer items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {searching ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                "Search"
              )}
            </button>
            <button
              type="button"
              onClick={handleClear}
              className="inline-flex h-10 cursor-pointer items-center justify-center rounded-md border border-input bg-card px-4 text-sm font-medium text-foreground hover:bg-accent"
            >
              Clear
            </button>
          </form>
          {searchError && (
            <p className="text-sm text-glory-red-500 dark:text-glory-red-400">
              {searchError}
            </p>
          )}

          {/* Search results */}
          {searchResult && searchResult.members.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">
                {searchResult.state_name}
                {searchResult.district
                  ? `, District ${searchResult.district}`
                  : ""}
              </p>
              {searchResult.members.map((member) => (
                <RepCard
                  key={member.bioguide_id}
                  member={member}
                  isFollowed={followedIds.has(member.bioguide_id)}
                  onFollow={() => handleFollow(member.bioguide_id)}
                  onUnfollow={() => handleUnfollow(member.bioguide_id)}
                  isPending={pendingId === member.bioguide_id}
                />
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
