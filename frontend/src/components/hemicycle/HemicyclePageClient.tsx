"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import type { Seat, SeatWithVote, VoteSummary } from "@/types";
import { getSeatVoteOverlayClient } from "@/lib/api";
import { cn, formatDate, getResultLabel, getResultBgColor } from "@/lib/utils";
import HemicycleChart from "./HemicycleChart";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface HemicyclePageClientProps {
  chamber: "house" | "senate";
  initialSeats: Seat[];
  votes: VoteSummary[];
}

export default function HemicyclePageClient({
  chamber,
  initialSeats,
  votes,
}: HemicyclePageClientProps) {
  const [selectedVoteId, setSelectedVoteId] = useState<string>("");

  const { data: overlaySeats, isFetching } = useQuery({
    queryKey: ["seat-vote-overlay", chamber, selectedVoteId],
    queryFn: () => getSeatVoteOverlayClient(chamber, selectedVoteId),
    enabled: !!selectedVoteId,
    staleTime: 5 * 60 * 1000,
  });

  const displaySeats: Seat[] | SeatWithVote[] =
    selectedVoteId && overlaySeats ? overlaySeats : initialSeats;
  const isOverlay = !!selectedVoteId && !!overlaySeats;
  const selectedVote = votes.find((v) => v.vote_id === selectedVoteId);

  return (
    <div className="flex h-full flex-col gap-4">
      {/* Vote selector + legend — compact, doesn't grow */}
      <div className="shrink-0 space-y-3">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <label
            htmlFor="vote-select"
            className="text-sm font-medium text-foreground"
          >
            Vote Overlay:
          </label>
          <Select
            value={selectedVoteId || "__default__"}
            onValueChange={(value) => setSelectedVoteId(value === "__default__" ? "" : value)}
          >
            <SelectTrigger className="max-w-lg">
              <SelectValue placeholder="Show by party (default)" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__default__">Show by party (default)</SelectItem>
              {votes.map((vote) => (
                <SelectItem key={vote.vote_id} value={vote.vote_id}>
                  {formatDate(vote.date)} — {vote.question} (
                  {getResultLabel(vote.result)})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {isFetching && (
            <span className="text-sm text-muted-foreground animate-pulse">
              Loading overlay...
            </span>
          )}
        </div>

        {/* Legend */}
        {isOverlay ? (
          <div className="flex flex-wrap gap-4 text-sm text-foreground">
            <div className="flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded-full border border-border bg-card" />
              <span>Yea</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: "#18181b" }} />
              <span>Nay</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded-full bg-yellow-500" />
              <span>Present</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded-full bg-gray-500" />
              <span>Not Voting</span>
            </div>
            <div className="ml-2 flex items-center gap-1.5 border-l border-border pl-3">
              <span className="text-muted-foreground">
                Aura = party color
              </span>
            </div>
          </div>
        ) : (
          <div className="flex flex-wrap gap-4 text-sm text-foreground">
            <div className="flex items-center gap-1.5">
              <span
                className="inline-block h-3 w-3 rounded-full"
                style={{ backgroundColor: "#2563eb" }}
              />
              <span>Democrat</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span
                className="inline-block h-3 w-3 rounded-full"
                style={{ backgroundColor: "#dc2626" }}
              />
              <span>Republican</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span
                className="inline-block h-3 w-3 rounded-full"
                style={{ backgroundColor: "#7c3aed" }}
              />
              <span>Independent</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded-full bg-secondary" />
              <span>Vacant</span>
            </div>
          </div>
        )}

        {/* Selected vote info */}
        {selectedVote && (
          <Card className="bg-secondary p-3 py-3 text-sm">
            <p className="font-medium text-foreground">
              {selectedVote.question}
            </p>
            <p className="mt-1 text-muted-foreground">
              {formatDate(selectedVote.date)} &mdash;{" "}
              <Badge className={cn("px-1.5", getResultBgColor(selectedVote.result))}>
                {getResultLabel(selectedVote.result)}
              </Badge>{" "}
              &mdash; Yea: {selectedVote.total_yea}, Nay:{" "}
              {selectedVote.total_nay}
            </p>
          </Card>
        )}
      </div>

      {/* Hemicycle chart — fills remaining space */}
      <div className="min-h-0 flex-1">
        <HemicycleChart
          chamber={chamber}
          seats={displaySeats}
          showVoteOverlay={isOverlay}
        />
      </div>
    </div>
  );
}
