"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";

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
const VIEWBOX = {
  senate: { minX: -70, minY: 30, width: 940, height: 290 },
  house: { minX: -30, minY: -80, width: 860, height: 450 },
};

const SEAT_RADIUS = {
  senate: 8,
  house: 4.5,
};

// Nay uses the card background color so dots "disappear" behind the party aura.
// We expose it as a CSS variable so it adapts to dark mode.
const NAY_COLOR_VAR = "var(--hemicycle-bg)";

// Inner dot color when vote overlay is active
function getVotePositionFillColor(position: VotePosition | null): string {
  if (!position) return "#d1d5db"; // gray-300 for no data
  const colors: Record<VotePosition, string> = {
    yea: "#ffffff",    // white = voted yes
    nay: NAY_COLOR_VAR, // matches card background via CSS variable
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
  votePosition?: VotePosition | null;
}

interface HemicycleChartProps {
  chamber: "house" | "senate";
  seats: Seat[] | SeatWithVote[];
  showVoteOverlay?: boolean;
}

export default function HemicycleChart({
  chamber,
  seats,
  showVoteOverlay = false,
}: HemicycleChartProps) {
  const router = useRouter();
  const [tooltip, setTooltip] = useState<TooltipData | null>(null);

  const viewBox = VIEWBOX[chamber];
  const seatRadius = SEAT_RADIUS[chamber];

  const handleSeatClick = useCallback(
    (seat: Seat | SeatWithVote) => {
      if (seat.member) {
        router.push(getMemberRoute(seat.member.bioguide_id, chamber));
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

      setTooltip({
        x,
        y,
        name: seat.member.full_name,
        party: seat.member.party,
        state: seat.member.state,
        district: seat.member.district,
        chamber,
        votePosition:
          "vote_position" in seat ? seat.vote_position : undefined,
      });
    },
    [chamber]
  );

  const handleMouseLeave = useCallback(() => {
    setTooltip(null);
  }, []);

  const getFillColor = (seat: Seat | SeatWithVote): string => {
    if (!seat.member) return "#e5e7eb";

    if (showVoteOverlay && "vote_position" in seat) {
      return getVotePositionFillColor(seat.vote_position);
    }

    return getPartyColor(seat.member.party);
  };

  return (
    <div className="relative h-full w-full">
      <svg
        viewBox={`${viewBox.minX} ${viewBox.minY} ${viewBox.width} ${viewBox.height}`}
        className="h-full w-full"
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label={`${chamber === "senate" ? "Senate" : "House"} hemicycle seating chart`}
      >
        {seats.map((seat) => {
          const isOverlay =
            showVoteOverlay && seat.member && "vote_position" in seat;
          const partyColor = seat.member
            ? getPartyColor(seat.member.party)
            : "#e5e7eb";

          return (
            <g
              key={seat.seat_id}
              className={
                seat.member
                  ? "cursor-pointer transition-opacity hover:opacity-80"
                  : ""
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
              {/* Aura — party-colored outer glow, only in overlay mode */}
              {isOverlay && (
                <circle
                  cx={seat.svg_x}
                  cy={seat.svg_y}
                  r={seatRadius * AURA_MULTIPLIER}
                  fill={partyColor}
                  opacity={0.35}
                />
              )}
              {/* Inner dot — party color normally, vote position in overlay */}
              <circle
                cx={seat.svg_x}
                cy={seat.svg_y}
                r={seatRadius}
                fill={
                  isOverlay
                    ? getVotePositionFillColor(
                        (seat as SeatWithVote).vote_position
                      )
                    : partyColor
                }
                stroke={isOverlay ? partyColor : seat.member ? "#ffffff" : "none"}
                strokeWidth={isOverlay ? 0.8 : seat.member ? 0.5 : 0}
              />
            </g>
          );
        })}
      </svg>

      {tooltip && (
        <div
          className="pointer-events-none absolute z-10 rounded-lg bg-zinc-900 px-3 py-2 text-sm text-white shadow-lg"
          style={{
            left: tooltip.x,
            top: tooltip.y - 60,
            transform: "translateX(-50%)",
          }}
        >
          <p className="font-semibold">{tooltip.name}</p>
          <p className="text-zinc-300">
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
      )}
    </div>
  );
}
