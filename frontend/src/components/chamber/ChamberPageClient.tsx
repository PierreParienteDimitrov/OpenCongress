"use client";

import { useState } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { Landmark, Map, List } from "lucide-react";

import type {
  MemberListItem,
  PaginatedResponse,
  Seat,
  VoteSummary,
} from "@/types";
import {
  getSenatorsPaginated,
  getRepresentativesPaginated,
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
  const [selectedVoteId, setSelectedVoteId] = useState<string>("");

  function handleTabChange(value: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (value === "seats") {
      params.delete("view");
    } else {
      params.set("view", value);
    }
    const query = params.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, {
      scroll: false,
    });
  }

  const isSeats = currentView === "seats";

  return (
    <main
      className={cn(
        "flex flex-col bg-background",
        isSeats
          ? "h-[calc(100vh-var(--navbar-height))]"
          : "min-h-screen"
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
        <div className="mt-3 flex flex-wrap items-center gap-3">
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
          {isSeats && (
            <Select
              value={selectedVoteId || "__default__"}
              onValueChange={(value) =>
                setSelectedVoteId(value === "__default__" ? "" : value)
              }
            >
              <SelectTrigger className="w-auto max-w-xs sm:max-w-md">
                <SelectValue placeholder="Show by party (default)" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__default__">
                  Show by party (default)
                </SelectItem>
                {votes.map((vote) => (
                  <SelectItem key={vote.vote_id} value={vote.vote_id}>
                    {formatDate(vote.date)} — {vote.question} (
                    {getResultLabel(vote.result)})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>
      </GridContainer>

      {/* Content — layout depends on active tab */}
      {isSeats ? (
        <div className="min-h-0 flex-1">
          <HemicyclePageClient
            chamber={chamber}
            initialSeats={initialSeats}
            votes={votes}
            selectedVoteId={selectedVoteId}
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
