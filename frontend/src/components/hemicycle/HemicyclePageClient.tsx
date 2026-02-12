"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import type { Seat, SeatWithVote, VoteSummary } from "@/types";
import { getSeatVoteOverlayClient } from "@/lib/api";
import { formatDate, getResultLabel, getResultBgColor } from "@/lib/utils";
import HemicycleChart from "./HemicycleChart";

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
            className="text-sm font-medium text-zinc-700 dark:text-zinc-300"
          >
            Vote Overlay:
          </label>
          <select
            id="vote-select"
            value={selectedVoteId}
            onChange={(e) => setSelectedVoteId(e.target.value)}
            className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-100 max-w-lg"
          >
            <option value="">Show by party (default)</option>
            {votes.map((vote) => (
              <option key={vote.vote_id} value={vote.vote_id}>
                {formatDate(vote.date)} — {vote.question} (
                {getResultLabel(vote.result)})
              </option>
            ))}
          </select>
          {isFetching && (
            <span className="text-sm text-zinc-500 animate-pulse">
              Loading overlay...
            </span>
          )}
        </div>

        {/* Legend */}
        {isOverlay ? (
          <div className="flex flex-wrap gap-4 text-sm text-zinc-700 dark:text-zinc-300">
            <div className="flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded-full border border-zinc-300 bg-white dark:border-zinc-500" />
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
            <div className="ml-2 flex items-center gap-1.5 border-l border-zinc-300 pl-3 dark:border-zinc-600">
              <span className="text-zinc-500 dark:text-zinc-400">
                Aura = party color
              </span>
            </div>
          </div>
        ) : (
          <div className="flex flex-wrap gap-4 text-sm text-zinc-700 dark:text-zinc-300">
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
              <span className="inline-block h-3 w-3 rounded-full bg-gray-200 dark:bg-gray-600" />
              <span>Vacant</span>
            </div>
          </div>
        )}

        {/* Selected vote info */}
        {selectedVote && (
          <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-sm dark:border-zinc-700 dark:bg-zinc-800">
            <p className="font-medium text-zinc-900 dark:text-zinc-100">
              {selectedVote.question}
            </p>
            <p className="mt-1 text-zinc-600 dark:text-zinc-400">
              {formatDate(selectedVote.date)} &mdash;{" "}
              <span
                className={`rounded px-1.5 py-0.5 text-xs font-medium ${getResultBgColor(selectedVote.result)}`}
              >
                {getResultLabel(selectedVote.result)}
              </span>{" "}
              &mdash; Yea: {selectedVote.total_yea}, Nay:{" "}
              {selectedVote.total_nay}
            </p>
          </div>
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
