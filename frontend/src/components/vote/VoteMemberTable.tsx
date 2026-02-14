"use client";

import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import Link from "next/link";

import type { SeatWithVote } from "@/types";
import {
  cn,
  getPartyBgColor,
  getPartyName,
  getPositionBgColor,
  getPositionLabel,
} from "@/lib/utils";
import { getMemberRoute } from "@/lib/routes";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface VoteMemberTableProps {
  seats: SeatWithVote[];
  chamber: "house" | "senate";
}

export default function VoteMemberTable({
  seats,
  chamber,
}: VoteMemberTableProps) {
  const [search, setSearch] = useState("");
  const [positionFilter, setPositionFilter] = useState<string>("all");

  const members = useMemo(() => {
    // Extract seats that have a member assigned
    const withMembers = seats.filter((s) => s.member);

    // Sort alphabetically by full_name
    withMembers.sort((a, b) =>
      a.member!.full_name.localeCompare(b.member!.full_name)
    );

    // Apply search filter
    let filtered = withMembers;
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      filtered = filtered.filter(
        (s) =>
          s.member!.full_name.toLowerCase().includes(q) ||
          s.member!.state.toLowerCase().includes(q)
      );
    }

    // Apply position filter
    if (positionFilter !== "all") {
      filtered = filtered.filter(
        (s) => s.vote_position === positionFilter
      );
    }

    return filtered;
  }, [seats, search, positionFilter]);

  // Counts for filter buttons
  const counts = useMemo(() => {
    const c = { all: 0, yea: 0, nay: 0, present: 0, not_voting: 0 };
    for (const s of seats) {
      if (!s.member) continue;
      c.all++;
      if (s.vote_position && s.vote_position in c) {
        c[s.vote_position as keyof typeof c]++;
      }
    }
    return c;
  }, [seats]);

  return (
    <div>
      {/* Search + Filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name or state..."
            className="h-9 w-full rounded-md border border-input bg-card pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-2 focus:ring-ring/50"
          />
        </div>
        <div className="flex flex-wrap gap-1.5">
          {(
            [
              ["all", "All"],
              ["yea", "Yea"],
              ["nay", "Nay"],
              ["present", "Present"],
              ["not_voting", "Not Voting"],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setPositionFilter(key)}
              className={cn(
                "rounded-md px-2.5 py-1 text-xs font-medium transition-colors",
                positionFilter === key
                  ? "bg-accent text-accent-foreground"
                  : "bg-secondary text-muted-foreground hover:text-foreground"
              )}
            >
              {label} ({counts[key]})
            </button>
          ))}
        </div>
      </div>

      {/* Count */}
      <p className="mb-3 text-sm text-muted-foreground">
        {members.length} member{members.length !== 1 ? "s" : ""}
      </p>

      {/* Table */}
      <div className="overflow-x-auto rounded-md border border-border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[50%]">Member</TableHead>
              <TableHead>Party</TableHead>
              <TableHead>State</TableHead>
              <TableHead className="text-right">Vote</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {members.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={4}
                  className="h-24 text-center text-muted-foreground"
                >
                  No members found.
                </TableCell>
              </TableRow>
            ) : (
              members.map((seat) => {
                const m = seat.member!;
                return (
                  <TableRow key={seat.seat_id}>
                    <TableCell>
                      <Link
                        href={getMemberRoute(m.bioguide_id, chamber)}
                        className="flex items-center gap-3 group"
                      >
                        {m.photo_url ? (
                          <img
                            src={m.photo_url}
                            alt={m.full_name}
                            className="h-8 w-8 rounded-full object-cover shrink-0"
                            loading="lazy"
                          />
                        ) : (
                          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-secondary shrink-0">
                            <span className="text-xs font-medium text-muted-foreground">
                              {m.full_name
                                .split(" ")
                                .map((n) => n[0])
                                .join("")
                                .slice(0, 2)}
                            </span>
                          </div>
                        )}
                        <span className="font-medium text-foreground group-hover:text-accent truncate">
                          {m.full_name}
                        </span>
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Badge className={cn("text-xs", getPartyBgColor(m.party))}>
                        {getPartyName(m.party)}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {m.state}
                    </TableCell>
                    <TableCell className="text-right">
                      {seat.vote_position ? (
                        <Badge
                          className={cn(
                            "text-xs",
                            getPositionBgColor(seat.vote_position)
                          )}
                        >
                          {getPositionLabel(seat.vote_position)}
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground text-xs">
                          —
                        </span>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
