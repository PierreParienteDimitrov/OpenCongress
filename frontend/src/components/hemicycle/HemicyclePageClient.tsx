"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import type { Seat, SeatWithVote, VoteSummary } from "@/types";
import { getSeatVoteOverlayClient } from "@/lib/api";
import { cn, formatDate, getResultLabel, getResultBgColor } from "@/lib/utils";
import HemicycleChart, { VIEWBOX } from "./HemicycleChart";
import { useMapZoom } from "@/components/map/useMapZoom";
import MapZoomControls from "@/components/map/MapZoomControls";
import { Badge } from "@/components/ui/badge";

interface HemicyclePageClientProps {
  chamber: "house" | "senate";
  initialSeats: Seat[];
  votes: VoteSummary[];
  selectedVoteId: string;
}

export default function HemicyclePageClient({
  chamber,
  initialSeats,
  votes,
  selectedVoteId,
}: HemicyclePageClientProps) {
  const vb = VIEWBOX[chamber];
  const extent = useMemo<[[number, number], [number, number]]>(
    () => [[vb.minX, vb.minY], [vb.minX + vb.width, vb.minY + vb.height]],
    [vb.minX, vb.minY, vb.width, vb.height]
  );
  const { svgRef, gRef, transform, isZoomed, zoomIn, zoomOut, resetZoom } =
    useMapZoom({ width: vb.width, height: vb.height, translateExtent: extent });

  const { data: overlaySeats } = useQuery({
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
    <div className="relative h-full">
      {/* Hemicycle chart — fills the entire area */}
      <MapZoomControls
        isZoomed={isZoomed}
        onZoomIn={zoomIn}
        onZoomOut={zoomOut}
        onReset={resetZoom}
      />
      <HemicycleChart
        chamber={chamber}
        seats={displaySeats}
        showVoteOverlay={isOverlay}
        svgRef={svgRef}
        gRef={gRef}
        zoomTransform={transform}
      />

      {/* Legend — overlaid at the bottom center of the hemicycle */}
      <div className="pointer-events-none absolute inset-x-0 bottom-2 flex justify-center">
        <div className="pointer-events-auto flex flex-wrap justify-center gap-x-4 gap-y-1 rounded-md bg-background/80 px-3 py-1.5 text-xs text-foreground backdrop-blur-sm">
          {isOverlay ? (
            <>
              <div className="flex items-center gap-1.5">
                <span className="inline-block h-2.5 w-2.5 rounded-full border border-border bg-card" />
                <span>Yea</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: "#18181b" }} />
                <span>Nay</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="inline-block h-2.5 w-2.5 rounded-full bg-yellow-500" />
                <span>Present</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="inline-block h-2.5 w-2.5 rounded-full bg-gray-500" />
                <span>Not Voting</span>
              </div>
              <div className="flex items-center gap-1.5 border-l border-border pl-3">
                <span className="text-muted-foreground">Border = party</span>
              </div>
            </>
          ) : (
            <>
              <div className="flex items-center gap-1.5">
                <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: "#2563eb" }} />
                <span>Democrat</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: "#dc2626" }} />
                <span>Republican</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: "#7c3aed" }} />
                <span>Independent</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="inline-block h-2.5 w-2.5 rounded-full bg-secondary" />
                <span>Vacant</span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Selected vote info — overlaid at top left */}
      {selectedVote && (
        <div className="absolute left-4 top-2 max-w-sm rounded-md bg-background/80 px-3 py-2 text-sm backdrop-blur-sm">
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
        </div>
      )}
    </div>
  );
}
