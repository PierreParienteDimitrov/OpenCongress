"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import type { ZoomTransform } from "d3-zoom";

import type { Seat, SeatWithVote, VotePosition } from "@/types";
import { getMemberRoute } from "@/lib/routes";
import {
  getPartyColor,
  getPartyName,
  getMemberLocation,
  getPositionLabel,
} from "@/lib/utils";

// viewBox origin + dimensions computed from generate_seats coordinates:
// House: center=(400,350), max radius=420 → coords span ~(-20..820, -70..350)
// Senate: center=(400,300), max radius=260 → coords span ~(-60..860, 40..300)
// Adding padding around the full range to prevent clipping.
export const VIEWBOX = {
  senate: { minX: -70, minY: 30, width: 940, height: 290 },
  house: { minX: -30, minY: -80, width: 860, height: 450 },
};

const SEAT_RADIUS = {
  senate: 8,
  house: 4.5,
};

// Inner dot color when vote overlay is active
function getVotePositionFillColor(position: VotePosition | null): string {
  if (!position) return "#d1d5db"; // gray-300 for no data
  const colors: Record<VotePosition, string> = {
    yea: "#ffffff",    // white = voted yes
    nay: "#18181b",    // dark = voted no
    present: "#eab308", // yellow-500
    not_voting: "#6b7280", // gray-500
  };
  return colors[position] ?? "#d1d5db";
}

// Aura radius multiplier (outer circle relative to inner)
const AURA_MULTIPLIER = 1.4;

interface TooltipData {
  x: number;
  y: number;
  name: string;
  party: string;
  state: string;
  district: number | null;
  chamber: "house" | "senate";
  photoUrl: string;
  votePosition?: VotePosition | null;
}

interface HemicycleChartProps {
  chamber: "house" | "senate";
  seats: Seat[] | SeatWithVote[];
  showVoteOverlay?: boolean;
  /** Callback ref from useMapZoom — enables d3-zoom on the SVG */
  svgRef?: (node: SVGSVGElement | null) => void;
  /** Ref for the <g> that receives the zoom transform */
  gRef?: React.RefObject<SVGGElement | null>;
  /** Current d3-zoom transform (for adjusting stroke widths & tooltip) */
  zoomTransform?: ZoomTransform;
}

// Hover radius multiplier — enlarges the seat to show the photo
const HOVER_RADIUS = {
  senate: 20,
  house: 14,
};

// Party color overlay opacity on default photo seats (low enough to see face)
const PHOTO_OVERLAY_OPACITY = 0.45;

export default function HemicycleChart({
  chamber,
  seats,
  showVoteOverlay = false,
  svgRef: externalSvgRef,
  gRef: externalGRef,
  zoomTransform,
}: HemicycleChartProps) {
  const router = useRouter();
  const [tooltip, setTooltip] = useState<TooltipData | null>(null);
  const [hoveredSeatId, setHoveredSeatId] = useState<string | null>(null);

  const viewBox = VIEWBOX[chamber];
  const seatRadius = SEAT_RADIUS[chamber];
  const k = zoomTransform?.k ?? 1; // current zoom scale

  const handleSeatClick = useCallback(
    (seat: Seat | SeatWithVote) => {
      if (seat.member) {
        router.push(getMemberRoute(seat.member.bioguide_id, chamber, seat.member.full_name));
      }
    },
    [router, chamber]
  );

  const handleMouseEnter = useCallback(
    (seat: Seat | SeatWithVote, event: React.MouseEvent<SVGCircleElement>) => {
      if (!seat.member) return;
      const svg = event.currentTarget.ownerSVGElement;
      if (!svg) return;
      const rect = svg.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;

      setHoveredSeatId(seat.seat_id);
      setTooltip({
        x,
        y,
        name: seat.member.full_name,
        party: seat.member.party,
        state: seat.member.state,
        district: seat.member.district,
        chamber,
        photoUrl: seat.member.photo_url,
        votePosition:
          "vote_position" in seat ? seat.vote_position : undefined,
      });
    },
    [chamber]
  );

  const handleMouseLeave = useCallback(() => {
    setHoveredSeatId(null);
    setTooltip(null);
  }, []);

  return (
    <div className="relative h-full w-full">
      <svg
        ref={externalSvgRef}
        viewBox={`${viewBox.minX} ${viewBox.minY} ${viewBox.width} ${viewBox.height}`}
        className={`h-full w-full ${externalSvgRef ? "cursor-grab touch-none" : ""}`}
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label={`${chamber === "senate" ? "Senate" : "House"} hemicycle seating chart`}
      >
        <g ref={externalGRef}>
        {/* Clip path definitions for all member seats (photos) */}
        <defs>
          {seats.map((seat) => {
            if (!seat.member) return null;
            return (
              <clipPath key={`clip-${seat.seat_id}`} id={`seat-clip-${seat.seat_id}`}>
                <circle cx={seat.svg_x} cy={seat.svg_y} r={seatRadius} />
              </clipPath>
            );
          })}
          {/* Clip paths for aura-sized photos in vote overlay mode */}
          {showVoteOverlay && seats.map((seat) => {
            if (!seat.member) return null;
            return (
              <clipPath key={`aura-clip-${seat.seat_id}`} id={`seat-aura-clip-${seat.seat_id}`}>
                <circle cx={seat.svg_x} cy={seat.svg_y} r={seatRadius * AURA_MULTIPLIER} />
              </clipPath>
            );
          })}
        </defs>

        {seats.map((seat) => {
          const isOverlay =
            showVoteOverlay && seat.member && "vote_position" in seat;
          const partyColor = seat.member
            ? getPartyColor(seat.member.party)
            : "#e5e7eb";
          const isHovered = seat.seat_id === hoveredSeatId;

          return (
            <g
              key={seat.seat_id}
              className={
                seat.member ? "cursor-pointer" : ""
              }
              onClick={() => handleSeatClick(seat)}
              onMouseEnter={(e) => {
                // Forward the event — find the nearest circle for positioning
                const circle = e.currentTarget.querySelector("circle");
                if (circle) {
                  handleMouseEnter(
                    seat,
                    e as unknown as React.MouseEvent<SVGCircleElement>
                  );
                }
              }}
              onMouseLeave={handleMouseLeave}
            >
              {seat.member && !isOverlay ? (
                /* Default view: member photo with party color tint */
                <g
                  opacity={isHovered ? 0 : 1}
                  style={{ transition: "opacity 150ms ease-out" }}
                >
                  {/* White background behind photo */}
                  <circle
                    cx={seat.svg_x}
                    cy={seat.svg_y}
                    r={seatRadius}
                    fill="#ffffff"
                  />
                  {/* Member photo clipped to seat circle */}
                  <image
                    href={seat.member.photo_url}
                    x={seat.svg_x - seatRadius}
                    y={seat.svg_y - seatRadius}
                    width={seatRadius * 2}
                    height={seatRadius * 2}
                    clipPath={`url(#seat-clip-${seat.seat_id})`}
                    preserveAspectRatio="xMidYMid slice"
                  />
                  {/* Party color overlay — low opacity to see the face */}
                  <circle
                    cx={seat.svg_x}
                    cy={seat.svg_y}
                    r={seatRadius}
                    fill={partyColor}
                    opacity={PHOTO_OVERLAY_OPACITY}
                  />
                  {/* Border ring */}
                  <circle
                    cx={seat.svg_x}
                    cy={seat.svg_y}
                    r={seatRadius}
                    fill="none"
                    stroke={partyColor}
                    strokeWidth={0.5 / k}
                  />
                </g>
              ) : isOverlay && seat.member ? (
                /* Vote overlay with member photo: photo fills the aura circle, vote color tint */
                <g
                  opacity={isHovered ? 0 : 1}
                  style={{ transition: "opacity 150ms ease-out" }}
                >
                  {/* White background behind photo */}
                  <circle
                    cx={seat.svg_x}
                    cy={seat.svg_y}
                    r={seatRadius * AURA_MULTIPLIER}
                    fill="#ffffff"
                  />
                  {/* Member photo clipped to aura-sized circle */}
                  <image
                    href={seat.member.photo_url}
                    x={seat.svg_x - seatRadius * AURA_MULTIPLIER}
                    y={seat.svg_y - seatRadius * AURA_MULTIPLIER}
                    width={seatRadius * AURA_MULTIPLIER * 2}
                    height={seatRadius * AURA_MULTIPLIER * 2}
                    clipPath={`url(#seat-aura-clip-${seat.seat_id})`}
                    preserveAspectRatio="xMidYMid slice"
                  />
                  {/* Vote color overlay — tints the photo with the vote position color */}
                  <circle
                    cx={seat.svg_x}
                    cy={seat.svg_y}
                    r={seatRadius * AURA_MULTIPLIER}
                    fill={getVotePositionFillColor(
                      (seat as SeatWithVote).vote_position
                    )}
                    opacity={PHOTO_OVERLAY_OPACITY}
                  />
                  {/* Border ring in party color */}
                  <circle
                    cx={seat.svg_x}
                    cy={seat.svg_y}
                    r={seatRadius * AURA_MULTIPLIER}
                    fill="none"
                    stroke={partyColor}
                    strokeWidth={0.8 / k}
                  />
                </g>
              ) : (
                /* Vacant seat: solid circle */
                <circle
                  cx={seat.svg_x}
                  cy={seat.svg_y}
                  r={seatRadius}
                  fill={partyColor}
                  stroke={seat.member ? "#ffffff" : "none"}
                  strokeWidth={(seat.member ? 0.5 : 0) / k}
                  opacity={isHovered ? 0 : 1}
                  style={{ transition: "opacity 150ms ease-out" }}
                />
              )}
            </g>
          );
        })}

        {/* Hovered seat — enlarged with profile photo + party color overlay */}
        {hoveredSeatId &&
          (() => {
            const seat = seats.find((s) => s.seat_id === hoveredSeatId);
            if (!seat?.member) return null;
            const r = HOVER_RADIUS[chamber];
            const partyColor = getPartyColor(seat.member.party);
            const clipId = `hover-clip-${seat.seat_id}`;
            return (
              <g
                className="pointer-events-none"
                style={{
                  transformOrigin: `${seat.svg_x}px ${seat.svg_y}px`,
                  animation: "hemicycle-hover-in 200ms ease-out both",
                }}
              >
                <defs>
                  <clipPath id={clipId}>
                    <circle cx={seat.svg_x} cy={seat.svg_y} r={r} />
                  </clipPath>
                </defs>
                {/* White background behind photo for transparency */}
                <circle
                  cx={seat.svg_x}
                  cy={seat.svg_y}
                  r={r}
                  fill="#ffffff"
                />
                {/* Member photo */}
                <image
                  href={seat.member.photo_url}
                  x={seat.svg_x - r}
                  y={seat.svg_y - r}
                  width={r * 2}
                  height={r * 2}
                  clipPath={`url(#${clipId})`}
                  preserveAspectRatio="xMidYMid slice"
                />
                {/* Party color overlay */}
                <circle
                  cx={seat.svg_x}
                  cy={seat.svg_y}
                  r={r}
                  fill={partyColor}
                  opacity={0.3}
                />
                {/* Border ring */}
                <circle
                  cx={seat.svg_x}
                  cy={seat.svg_y}
                  r={r}
                  fill="none"
                  stroke={partyColor}
                  strokeWidth={1.5 / k}
                />
              </g>
            );
          })()}
        </g>
      </svg>

      {tooltip && (
        <div
          className="pointer-events-none absolute z-10 flex items-center gap-2.5 rounded-lg bg-primary px-3 py-2 text-sm text-primary-foreground shadow-lg"
          style={{
            left: tooltip.x,
            top: tooltip.y - 70,
            transform: "translateX(-50%)",
          }}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={tooltip.photoUrl}
            alt=""
            className="h-10 w-10 shrink-0 rounded-full object-cover"
          />
          <div>
            <p className="font-semibold">{tooltip.name}</p>
            <p className="text-primary-foreground/70">
              {getPartyName(tooltip.party)} &mdash;{" "}
              {getMemberLocation(
                tooltip.state,
                tooltip.district,
                tooltip.chamber
              )}
            </p>
            {tooltip.votePosition !== undefined && (
              <p className="mt-1 font-medium">
                {tooltip.votePosition
                  ? getPositionLabel(tooltip.votePosition)
                  : "No vote recorded"}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
