"use client";

import { useMemo } from "react";

import type { Seat, SeatWithVote } from "@/types";
import HemicycleChart, { VIEWBOX } from "./HemicycleChart";
import { useMapZoom } from "@/components/map/useMapZoom";
import MapZoomControls from "@/components/map/MapZoomControls";

interface HemicyclePageClientProps {
  chamber: "house" | "senate";
  initialSeats: Seat[] | SeatWithVote[];
  showVoteOverlay?: boolean;
}

export default function HemicyclePageClient({
  chamber,
  initialSeats,
  showVoteOverlay = false,
}: HemicyclePageClientProps) {
  const vb = VIEWBOX[chamber];
  const extent = useMemo<[[number, number], [number, number]]>(
    () => [[vb.minX, vb.minY], [vb.minX + vb.width, vb.minY + vb.height]],
    [vb.minX, vb.minY, vb.width, vb.height]
  );
  const { svgRef, gRef, transform, isZoomed, zoomIn, zoomOut, resetZoom } =
    useMapZoom({ width: vb.width, height: vb.height, translateExtent: extent });

  return (
    <div className="relative h-full">
      <MapZoomControls
        isZoomed={isZoomed}
        onZoomIn={zoomIn}
        onZoomOut={zoomOut}
        onReset={resetZoom}
      />
      <HemicycleChart
        chamber={chamber}
        seats={initialSeats}
        showVoteOverlay={showVoteOverlay}
        svgRef={svgRef}
        gRef={gRef}
        zoomTransform={transform}
      />

      {/* Legend — overlaid at the bottom center of the hemicycle */}
      <div className="pointer-events-none absolute inset-x-0 bottom-3 flex justify-center">
        <div className="pointer-events-auto flex flex-wrap justify-center gap-x-5 gap-y-1 rounded-md bg-background/80 px-4 py-2 text-sm text-foreground backdrop-blur-sm">
          {showVoteOverlay ? (
            <>
              <div className="flex items-center gap-2">
                <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: "#ffffff", border: "1px solid #a1a1aa" }} />
                <span>Yea</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: "#18181b" }} />
                <span>Nay</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: "#eab308" }} />
                <span>Present</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: "#6b7280" }} />
                <span>Not Voting</span>
              </div>
            </>
          ) : (
            <>
              <div className="flex items-center gap-2">
                <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: "oklch(0.45 0.11 256)" }} />
                <span>Democrat</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: "oklch(0.498 0.185 14)" }} />
                <span>Republican</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: "#7c3aed" }} />
                <span>Independent</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="inline-block h-3 w-3 rounded-full bg-secondary" />
                <span>Vacant</span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
