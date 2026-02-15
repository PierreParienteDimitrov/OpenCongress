"use client";

import type { ReactNode } from "react";
import Link from "next/link";

import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  cn,
  getResultBgColor,
  getResultLabel,
} from "@/lib/utils";
import type { SeatWithVote, VoteSummary } from "@/types";
import { routes } from "@/lib/routes";
import HemicycleWithZoom from "@/components/hemicycle/HemicycleWithZoom";
import VoteMemberTable from "@/components/vote/VoteMemberTable";

interface VoteDetailContentProps {
  vote: VoteSummary;
  overlaySeats: SeatWithVote[];
  /** Left-column metadata (server-rendered) */
  sidebar: ReactNode;
}

export default function VoteDetailContent({
  vote,
  overlaySeats,
  sidebar,
}: VoteDetailContentProps) {
  const totalVotes = vote.total_yea + vote.total_nay;
  const yeaPercent = totalVotes > 0 ? (vote.total_yea / totalVotes) * 100 : 0;

  return (
    <Tabs defaultValue="overview">
      <TabsList variant="line">
        <TabsTrigger value="overview" className="cursor-pointer">
          Overview
        </TabsTrigger>
        {overlaySeats.length > 0 && (
          <TabsTrigger value="detail" className="cursor-pointer">
            Detail
          </TabsTrigger>
        )}
      </TabsList>

      {/* ── Overview tab — 3-column layout ── */}
      <TabsContent value="overview" className="pt-6">
        <div className="grid grid-cols-1 lg:grid-cols-[240px_1fr_280px] gap-6 lg:gap-8">
          {/* Left column — Vote metadata (passed from server) */}
          <div>{sidebar}</div>

          {/* Center column — Copy / description */}
          <div className="lg:border-l lg:border-r lg:border-border lg:px-8">
            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
              Question
            </h3>
            <p className="font-domine text-base text-foreground/80 leading-relaxed">
              {vote.question}
              {vote.bill_display_number && (
                <>
                  {" — "}
                  <Link
                    href={routes.legislation.detail(vote.bill_id!)}
                    className="cursor-pointer text-accent hover:text-accent/80"
                  >
                    {vote.bill_display_number}
                  </Link>
                </>
              )}
            </p>

            {vote.bill_title && (
              <>
                <Separator className="my-5" />
                <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
                  Bill Title
                </h3>
                <p className="font-domine text-base text-foreground/80 leading-relaxed">
                  {vote.bill_title}
                </p>
              </>
            )}

            {vote.ai_summary && (
              <>
                <Separator className="my-5" />
                <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
                  Summary
                </h3>
                <div className="space-y-3 font-domine text-base text-foreground/80 leading-relaxed">
                  {vote.ai_summary.split("\n").map((para, i) => (
                    <p key={i}>{para}</p>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground/60 mt-3">
                  AI-generated summary
                </p>
              </>
            )}
          </div>

          {/* Right column — Metrics */}
          <div>
            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
              Results
            </h3>

            {/* Result badge */}
            <div className="flex flex-wrap items-center gap-2 mb-4">
              <Badge
                className={cn("text-sm px-3 py-1", getResultBgColor(vote.result))}
              >
                {getResultLabel(vote.result)}
              </Badge>
              {vote.is_bipartisan && (
                <Badge className="bg-violet-600 text-white">Bipartisan</Badge>
              )}
            </div>

            {/* Vote bar */}
            <div className="mb-4">
              <div className="flex h-2 overflow-hidden bg-secondary">
                <div
                  className="bg-green-500 transition-all"
                  style={{ width: `${yeaPercent}%` }}
                />
                <div
                  className="bg-glory-red-500 transition-all"
                  style={{ width: `${100 - yeaPercent}%` }}
                />
              </div>
              <div className="flex justify-between text-xs mt-1.5">
                <span className="text-green-600 dark:text-green-400 font-medium">
                  Yea: {vote.total_yea}
                </span>
                <span className="text-glory-red-500 dark:text-glory-red-400 font-medium">
                  Nay: {vote.total_nay}
                </span>
              </div>
            </div>

            {/* Totals grid */}
            <div className="grid grid-cols-2 gap-2 mb-4">
              <div className="flex flex-col items-center gap-1 rounded-sm bg-white/90 dark:bg-white/10 p-3">
                <span className="text-2xl font-bold text-foreground">
                  {vote.total_yea}
                </span>
                <span className="text-xs font-medium text-muted-foreground">
                  Yea
                </span>
              </div>
              <div
                className="flex flex-col items-center gap-1 rounded-sm p-3"
                style={{ backgroundColor: "#18181b" }}
              >
                <span className="text-2xl font-bold text-white">
                  {vote.total_nay}
                </span>
                <span className="text-xs font-medium text-white/60">Nay</span>
              </div>
              <div className="flex flex-col items-center gap-1 rounded-sm bg-yellow-500/20 p-3">
                <span className="text-2xl font-bold text-foreground">
                  {vote.total_present}
                </span>
                <span className="text-xs font-medium text-muted-foreground">
                  Present
                </span>
              </div>
              <div className="flex flex-col items-center gap-1 rounded-sm bg-secondary p-3">
                <span className="text-2xl font-bold text-foreground">
                  {vote.total_not_voting}
                </span>
                <span className="text-xs font-medium text-muted-foreground">
                  Not Voting
                </span>
              </div>
            </div>

            {/* Party breakdown */}
            <div className="grid grid-cols-3 gap-3 text-xs">
              <div>
                <div className="font-medium text-glory-blue-500 dark:text-glory-blue-300">
                  Democrats
                </div>
                <div className="text-muted-foreground">
                  {vote.dem_yea} Y / {vote.dem_nay} N
                </div>
              </div>
              <div>
                <div className="font-medium text-glory-red-500 dark:text-glory-red-400">
                  Republicans
                </div>
                <div className="text-muted-foreground">
                  {vote.rep_yea} Y / {vote.rep_nay} N
                </div>
              </div>
              <div>
                <div className="font-medium text-violet-600 dark:text-violet-400">
                  Independents
                </div>
                <div className="text-muted-foreground">
                  {vote.ind_yea} Y / {vote.ind_nay} N
                </div>
              </div>
            </div>
          </div>
        </div>
      </TabsContent>

      {/* ── Detail tab — full width ── */}
      {overlaySeats.length > 0 && (
        <TabsContent value="detail" className="pt-6">
          {/* Seat Map */}
          <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
            Seat Map
          </h3>
          <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground mb-4">
            <div className="flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded-full border border-border bg-white" />
              <span>Yea</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span
                className="inline-block h-3 w-3 rounded-full"
                style={{ backgroundColor: "#18181b" }}
              />
              <span>Nay</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded-full bg-yellow-500" />
              <span>Present</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded-full bg-background0" />
              <span>Not Voting</span>
            </div>
            <div className="ml-2 flex items-center gap-1.5 border-l border-border pl-3">
              <span className="text-muted-foreground/60">
                Border = party color
              </span>
            </div>
          </div>
          <div className="h-[400px]">
            <HemicycleWithZoom
              chamber={vote.chamber}
              seats={overlaySeats}
              showVoteOverlay
            />
          </div>

          <Separator className="my-6" />

          {/* Member Votes Table */}
          <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
            Member Votes
          </h3>
          <VoteMemberTable seats={overlaySeats} chamber={vote.chamber} />
        </TabsContent>
      )}
    </Tabs>
  );
}
