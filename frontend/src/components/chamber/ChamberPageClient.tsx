"use client";

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
import { cn } from "@/lib/utils";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
        <div className="mt-3">
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
        </div>
      </GridContainer>

      {/* Content — layout depends on active tab */}
      {isSeats ? (
        <div className="min-h-0 flex-1 px-4 pb-4">
          <div className="flex h-full flex-col rounded-xl border border-border bg-card p-4 shadow-sm">
            <HemicyclePageClient
              chamber={chamber}
              initialSeats={initialSeats}
              votes={votes}
            />
          </div>
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
