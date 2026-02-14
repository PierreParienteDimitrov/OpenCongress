"use client";

import { useMemo } from "react";

import type { Seat, SeatWithVote } from "@/types";
import HemicycleChart, { VIEWBOX } from "./HemicycleChart";
import { useMapZoom } from "@/components/map/useMapZoom";
import MapZoomControls from "@/components/map/MapZoomControls";

interface HemicycleWithZoomProps {
  chamber: "house" | "senate";
  seats: Seat[] | SeatWithVote[];
  showVoteOverlay?: boolean;
}

export default function HemicycleWithZoom({
  chamber,
  seats,
  showVoteOverlay = false,
}: HemicycleWithZoomProps) {
  const vb = VIEWBOX[chamber];
  const extent = useMemo<[[number, number], [number, number]]>(
    () => [[vb.minX, vb.minY], [vb.minX + vb.width, vb.minY + vb.height]],
    [vb.minX, vb.minY, vb.width, vb.height]
  );
  const { svgRef, gRef, transform, isZoomed, zoomIn, zoomOut, resetZoom } =
    useMapZoom({ width: vb.width, height: vb.height, translateExtent: extent });

  return (
    <div className="relative h-full w-full">
      <MapZoomControls
        isZoomed={isZoomed}
        onZoomIn={zoomIn}
        onZoomOut={zoomOut}
        onReset={resetZoom}
      />
      <HemicycleChart
        chamber={chamber}
        seats={seats}
        showVoteOverlay={showVoteOverlay}
        svgRef={svgRef}
        gRef={gRef}
        zoomTransform={transform}
      />
    </div>
  );
}
