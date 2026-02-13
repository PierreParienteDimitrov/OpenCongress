"use client";

import { getPartyName, getMemberLocation } from "@/lib/utils";

export interface MapTooltipMember {
  name: string;
  party: string;
  state: string;
  district: number | null;
  chamber: "house" | "senate";
  bioguideId: string;
}

interface MapTooltipProps {
  x: number;
  y: number;
  members: MapTooltipMember[];
}

export default function MapTooltip({ x, y, members }: MapTooltipProps) {
  if (members.length === 0) return null;

  return (
    <div
      className="pointer-events-none absolute z-10 rounded-lg bg-primary px-3 py-2 text-sm text-primary-foreground shadow-lg"
      style={{
        left: x,
        top: y - 60,
        transform: "translateX(-50%)",
      }}
    >
      {members.map((member) => (
        <div key={member.bioguideId}>
          <p className="font-semibold">{member.name}</p>
          <p className="text-primary-foreground/70">
            {getPartyName(member.party)} &mdash;{" "}
            {getMemberLocation(member.state, member.district, member.chamber)}
          </p>
        </div>
      ))}
    </div>
  );
}
