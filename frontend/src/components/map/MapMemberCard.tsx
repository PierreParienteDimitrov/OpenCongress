"use client";

import Link from "next/link";

import type { MemberListItem } from "@/types";
import { cn, getPartyBgColor, getPartyName, getMemberLocation } from "@/lib/utils";
import { getMemberRoute } from "@/lib/routes";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface MapMemberCardProps {
  member: MemberListItem;
}

export default function MapMemberCard({ member }: MapMemberCardProps) {
  return (
    <Link href={getMemberRoute(member.bioguide_id, member.chamber)}>
      <Card className="group flex flex-row items-center gap-4 p-4 py-4 transition-all hover:border-muted-foreground/30 hover:shadow-md">
        <div className="shrink-0">
          {member.photo_url ? (
            <img
              src={member.photo_url}
              alt={member.full_name}
              className="h-12 w-12 rounded-full object-cover"
              loading="lazy"
            />
          ) : (
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-secondary">
              <span className="text-sm font-medium text-muted-foreground">
                {member.full_name
                  .split(" ")
                  .map((n) => n[0])
                  .join("")
                  .slice(0, 2)}
              </span>
            </div>
          )}
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="truncate font-semibold text-foreground group-hover:text-accent">
            {member.full_name}
          </h3>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            <Badge className={cn(getPartyBgColor(member.party))}>
              {getPartyName(member.party)}
            </Badge>
            <span className="text-sm text-muted-foreground">
              {getMemberLocation(member.state, member.district, member.chamber)}
            </span>
          </div>
        </div>
        <svg
          className="h-5 w-5 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-1 group-hover:text-foreground"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5l7 7-7 7"
          />
        </svg>
      </Card>
    </Link>
  );
}
