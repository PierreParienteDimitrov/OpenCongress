import Link from "next/link";
import { Users, FolderTree, FileText } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { routes } from "@/lib/routes";
import { cn } from "@/lib/utils";
import type { CommitteeListItem } from "@/types";

function getChamberBadgeColor(chamber: string): string {
  return chamber === "senate"
    ? "bg-glory-blue-500 text-white"
    : "bg-glory-red-500 text-white";
}

interface CommitteeCardProps {
  committee: CommitteeListItem;
}

export default function CommitteeCard({ committee }: CommitteeCardProps) {
  return (
    <Link
      href={routes.committees.detail(committee.committee_id, committee.name)}
      className="cursor-pointer"
    >
      <Card className="h-full py-4 transition-colors hover:bg-accent/50">
        <CardContent className="space-y-3">
          {/* Header: name + chamber badge */}
          <div className="flex items-start justify-between gap-2">
            <h3 className="text-sm font-semibold leading-tight text-foreground">
              {committee.name}
            </h3>
            <Badge
              className={cn(
                "shrink-0 text-xs",
                getChamberBadgeColor(committee.chamber)
              )}
            >
              {committee.chamber === "senate" ? "Senate" : "House"}
            </Badge>
          </div>

          {/* Leadership */}
          {committee.chair && (
            <p className="text-xs text-muted-foreground">
              <span className="font-medium text-foreground">Chair:</span>{" "}
              {committee.chair.full_name} ({committee.chair.party})
            </p>
          )}
          {committee.ranking_member && (
            <p className="text-xs text-muted-foreground">
              <span className="font-medium text-foreground">Ranking:</span>{" "}
              {committee.ranking_member.full_name} (
              {committee.ranking_member.party})
            </p>
          )}

          {/* Metrics row */}
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <Users className="size-3.5" />
              {committee.member_count} members
            </span>
            {committee.subcommittee_count > 0 && (
              <span className="flex items-center gap-1">
                <FolderTree className="size-3.5" />
                {committee.subcommittee_count} sub
              </span>
            )}
            {committee.referred_bills_count > 0 && (
              <span className="flex items-center gap-1">
                <FileText className="size-3.5" />
                {committee.referred_bills_count} bills
              </span>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
