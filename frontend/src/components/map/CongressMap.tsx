"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { ArrowLeft } from "lucide-react";

import type { MemberListItem, ZipLookupResult } from "@/types";
import { getStateName } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { GridContainer } from "@/components/layout/GridContainer";
import ZipCodeSearch from "./ZipCodeSearch";
import MapMemberCard from "./MapMemberCard";

// Dynamic imports to avoid SSR issues with d3-geo
const SenateMap = dynamic(() => import("./SenateMap"), {
  ssr: false,
  loading: () => <MapSkeleton />,
});

const DistrictMap = dynamic(() => import("./DistrictMap"), {
  ssr: false,
  loading: () => <MapSkeleton />,
});

function MapSkeleton() {
  return (
    <Skeleton className="aspect-[960/600] w-full rounded-lg bg-secondary" />
  );
}

interface CongressMapProps {
  members: MemberListItem[];
  chamber: "senate" | "house";
}

export default function CongressMap({ members, chamber }: CongressMapProps) {
  const [focusedState, setFocusedState] = useState<string | null>(null);
  const [zipMembers, setZipMembers] = useState<MemberListItem[]>([]);

  function handleZipResult(result: ZipLookupResult) {
    setFocusedState(result.state);
    setZipMembers(result.members);
  }

  function handleClear() {
    setFocusedState(null);
    setZipMembers([]);
  }

  return (
    <div className="flex h-full flex-col">
      <GridContainer className="w-full shrink-0 py-3">
        <ZipCodeSearch onResult={handleZipResult} onClear={handleClear} />

        {focusedState && (
          <div className="mt-3 flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={handleClear}>
              <ArrowLeft className="mr-1 size-4" />
              Back to full map
            </Button>
            <span className="text-sm text-muted-foreground">
              Viewing {getStateName(focusedState)}
            </span>
          </div>
        )}

        {zipMembers.length > 0 && (
          <div className="mt-4">
            <h3 className="mb-3 text-lg font-semibold text-foreground">
              Your {chamber === "senate" ? "Senators" : "Representatives"}
            </h3>
            <div className="grid gap-3 sm:grid-cols-2">
              {zipMembers.map((member) => (
                <MapMemberCard key={member.bioguide_id} member={member} />
              ))}
            </div>
          </div>
        )}
      </GridContainer>

      <div className="min-h-0 flex-1">
        {chamber === "senate" ? (
          <SenateMap members={members} focusedState={focusedState} />
        ) : (
          <DistrictMap members={members} focusedState={focusedState} />
        )}
      </div>
    </div>
  );
}
