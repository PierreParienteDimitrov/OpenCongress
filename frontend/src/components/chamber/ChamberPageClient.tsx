"use client";

import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Landmark, Map, List } from "lucide-react";

import type {
  MemberListItem,
  PaginatedResponse,
  Seat,
  SeatWithVote,
  VoteSummary,
} from "@/types";
import {
  getSenatorsPaginated,
  getRepresentativesPaginated,
  getSeatVoteOverlayClient,
} from "@/lib/api";
import { cn, formatDate, getResultLabel } from "@/lib/utils";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { GridContainer } from "@/components/layout/GridContainer";
import MemberList from "@/components/member/MemberList";
import CongressMap from "@/components/map/CongressMap";
import HemicyclePageClient from "@/components/hemicycle/HemicyclePageClient";

interface ChamberPageClientProps {
  chamber: "senate" | "house";
  initialData: PaginatedResponse<MemberListItem>;
  allMembers: MemberListItem[];
  initialSeats: Seat[];
  votes: VoteSummary[];
  memberCount: number;
}

const FETCH_FNS = {
  senate: getSenatorsPaginated,
  house: getRepresentativesPaginated,
};

const LABELS = {
  senate: {
    title: "U.S. Senate",
    desc: "members of the United States Senate",
  },
  house: {
    title: "U.S. House of Representatives",
    desc: "members of the U.S. House of Representatives",
  },
};

const DEFAULT_VOTE = "__default__";

export default function ChamberPageClient({
  chamber,
  initialData,
  allMembers,
  initialSeats,
  votes,
  memberCount,
}: ChamberPageClientProps) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const currentView = searchParams.get("view") ?? "seats";
  const selectedVoteId = searchParams.get("vote") ?? DEFAULT_VOTE;

  const { data: voteOverlaySeats } = useQuery<SeatWithVote[]>({
    queryKey: ["seat-vote-overlay", chamber, selectedVoteId],
    queryFn: () => getSeatVoteOverlayClient(chamber, selectedVoteId),
    enabled: selectedVoteId !== DEFAULT_VOTE,
  });

  function updateParam(key: string, value: string, defaultValue: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (value === defaultValue) {
      params.delete(key);
    } else {
      params.set(key, value);
    }
    const query = params.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, {
      scroll: false,
    });
  }

  function handleTabChange(value: string) {
    updateParam("view", value, "seats");
  }

  function handleVoteChange(value: string) {
    updateParam("vote", value, DEFAULT_VOTE);
  }

  const isSeats = currentView === "seats";
  const showVoteOverlay =
    selectedVoteId !== DEFAULT_VOTE && !!voteOverlaySeats;
  const displaySeats = showVoteOverlay ? voteOverlaySeats : initialSeats;

  return (
    <main
      className={cn(
        "flex flex-col bg-background",
        isSeats
          ? "h-[calc(100vh-var(--navbar-height))]"
          : "min-h-screen",
      )}
    >
      {/* Header + Tab bar */}
      <GridContainer className="shrink-0 pt-4 pb-2">
        <h1 className="text-2xl font-bold text-foreground sm:text-3xl">
          {LABELS[chamber].title}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Browse all {memberCount} current {LABELS[chamber].desc}.
        </p>
        <div className="mt-3 flex items-center justify-between gap-4">
          <Tabs value={currentView} onValueChange={handleTabChange}>
            <TabsList>
              <TabsTrigger value="seats">
                <Landmark className="mr-1.5 size-4" />
                Seats
              </TabsTrigger>
              <TabsTrigger value="map">
                <Map className="mr-1.5 size-4" />
                Map
              </TabsTrigger>
              <TabsTrigger value="list">
                <List className="mr-1.5 size-4" />
                List
              </TabsTrigger>
            </TabsList>
          </Tabs>

          {isSeats && votes.length > 0 && (
            <div className="flex flex-col items-end gap-1.5">
              <Select value={selectedVoteId} onValueChange={handleVoteChange}>
                <SelectTrigger className="w-[340px] cursor-pointer">
                  <SelectValue placeholder="Show by party (default)" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={DEFAULT_VOTE} className="cursor-pointer">
                    Show by party (default)
                  </SelectItem>
                  {votes.map((vote) => (
                    <SelectItem
                      key={vote.vote_id}
                      value={vote.vote_id}
                      className="cursor-pointer"
                    >
                      {formatDate(vote.date)} — {vote.question} (
                      {getResultLabel(vote.result)})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {showVoteOverlay && (
                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1.5">
                    <span className="inline-block size-2.5 rounded-full bg-white border border-zinc-400" />
                    <span>Yea</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="inline-block size-2.5 rounded-full bg-zinc-900" />
                    <span>Nay</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="inline-block size-2.5 rounded-full bg-yellow-500" />
                    <span>Present</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="inline-block size-2.5 rounded-full bg-gray-500" />
                    <span>Not Voting</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </GridContainer>

      {/* Content — layout depends on active tab */}
      {isSeats ? (
        <div className="min-h-0 flex-1">
          <HemicyclePageClient
            chamber={chamber}
            initialSeats={displaySeats}
            showVoteOverlay={showVoteOverlay}
          />
        </div>
      ) : currentView === "map" ? (
        <GridContainer className="py-4">
          <CongressMap members={allMembers} chamber={chamber} />
        </GridContainer>
      ) : (
        <GridContainer className="py-4">
          <MemberList
            chamber={chamber}
            initialData={initialData}
            fetchFn={FETCH_FNS[chamber]}
          />
        </GridContainer>
      )}
    </main>
  );
}
