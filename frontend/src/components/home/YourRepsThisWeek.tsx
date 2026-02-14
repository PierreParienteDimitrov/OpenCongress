"use client";

import { useSession } from "next-auth/react";
import { useQuery } from "@tanstack/react-query";
import Image from "next/image";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchRepActivity } from "@/lib/api-client";
import { getMemberRoute, routes } from "@/lib/routes";
import {
  cn,
  getPartyBgColor,
  getPositionBgColor,
  getPositionLabel,
  truncate,
} from "@/lib/utils";
import type { RepWeeklyActivity, MemberRecentVote } from "@/types";

export default function YourRepsThisWeek() {
  const { data: session, status } = useSession();

  const { data, isLoading } = useQuery({
    queryKey: ["rep-activity"],
    queryFn: fetchRepActivity,
    enabled: status === "authenticated",
    staleTime: 5 * 60 * 1000,
  });

  // Don't render anything for unauthenticated users
  if (status === "loading") return null;
  if (!session) return null;

  // Loading state
  if (isLoading) {
    return (
      <div className="pb-10">
        <h3 className="text-lg font-bold text-foreground">
          Your Reps This Week
        </h3>
        <div className="mt-3 space-y-4">
          {[1, 2].map((i) => (
            <div key={i} className="space-y-2">
              <div className="flex items-center gap-2">
                <Skeleton className="size-8 rounded-full bg-secondary" />
                <Skeleton className="h-4 w-24 bg-secondary" />
              </div>
              <Skeleton className="h-3 w-full bg-secondary" />
              <Skeleton className="h-3 w-3/4 bg-secondary" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  // No followed reps: show CTA
  if (!data || data.members.length === 0) {
    return (
      <div className="pb-10">
        <h3 className="text-lg font-bold text-foreground">
          Your Reps This Week
        </h3>
        <p className="mt-2 text-sm text-muted-foreground">
          Follow your representatives to see their weekly activity here.
        </p>
        <Link
          href={routes.settings.representatives}
          className="mt-2 inline-block cursor-pointer text-sm font-medium text-accent hover:underline"
        >
          Find Your Reps →
        </Link>
      </div>
    );
  }

  // Check if any member has activity
  const hasAnyActivity = data.members.some(
    (m) => m.recent_votes.length > 0 || m.sponsored_bills.length > 0,
  );

  if (!hasAnyActivity) {
    return (
      <div className="pb-10">
        <h3 className="text-lg font-bold text-foreground">
          Your Reps This Week
        </h3>
        <p className="mt-2 text-sm text-muted-foreground">
          No activity from your reps this week.
        </p>
      </div>
    );
  }

  return (
    <div className="pb-10">
      <h3 className="text-lg font-bold text-foreground">
        Your Reps This Week
      </h3>
      <div className="mt-3 space-y-5">
        {data.members
          .filter(
            (m) => m.recent_votes.length > 0 || m.sponsored_bills.length > 0,
          )
          .map((member) => (
            <RepActivityCard key={member.bioguide_id} member={member} />
          ))}
      </div>
    </div>
  );
}

function RepActivityCard({ member }: { member: RepWeeklyActivity }) {
  return (
    <div className="space-y-2">
      {/* Member header */}
      <Link
        href={getMemberRoute(member.bioguide_id, member.chamber)}
        className="group flex cursor-pointer items-center gap-2"
      >
        {member.photo_url ? (
          <Image
            src={member.photo_url}
            alt={member.full_name}
            width={32}
            height={32}
            className="size-8 rounded-full object-cover"
          />
        ) : (
          <div className="flex size-8 items-center justify-center rounded-full bg-secondary text-xs font-bold text-muted-foreground">
            {member.full_name.charAt(0)}
          </div>
        )}
        <div className="flex min-w-0 items-center gap-2">
          <span className="text-sm font-semibold text-foreground group-hover:text-accent">
            {member.full_name}
          </span>
          <Badge className={cn("text-xs", getPartyBgColor(member.party))}>
            {member.party}
          </Badge>
        </div>
      </Link>

      {/* Recent votes */}
      {member.recent_votes.length > 0 && (
        <div className="ml-10 space-y-1.5">
          {member.recent_votes.slice(0, 3).map((vote) => (
            <VoteRow key={vote.vote_id} vote={vote} />
          ))}
        </div>
      )}

      {/* Sponsored bills */}
      {member.sponsored_bills.length > 0 && (
        <div className="ml-10 space-y-1.5">
          {member.sponsored_bills.map((bill) => (
            <Link
              key={bill.bill_id}
              href={routes.legislation.detail(bill.bill_id)}
              className="block cursor-pointer text-xs text-muted-foreground hover:text-foreground"
            >
              <span className="font-medium text-foreground">
                {bill.display_number}
              </span>{" "}
              {truncate(bill.latest_action_text || bill.short_title, 50)}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function VoteRow({ vote }: { vote: MemberRecentVote }) {
  const href = vote.bill_id
    ? routes.legislation.detail(vote.bill_id)
    : routes.vote.detail(vote.vote_id);

  return (
    <Link
      href={href}
      className="-mx-1 flex cursor-pointer items-start gap-2 rounded px-1 py-0.5 text-xs hover:bg-accent/5"
    >
      <Badge
        className={cn(
          "mt-0.5 shrink-0 px-1.5 text-[10px]",
          getPositionBgColor(vote.position),
        )}
      >
        {getPositionLabel(vote.position)}
      </Badge>
      <span className="min-w-0 text-muted-foreground">
        {vote.bill_display_number && (
          <span className="font-medium text-foreground">
            {vote.bill_display_number}:{" "}
          </span>
        )}
        {truncate(vote.description, 50)}
      </span>
    </Link>
  );
}
