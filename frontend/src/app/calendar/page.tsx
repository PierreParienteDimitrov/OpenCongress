import Link from "next/link";
import { ChevronLeft } from "lucide-react";

import { ClickableCard } from "./ClickableCard";
import { getBillsCalendar, getVotesCalendar } from "@/lib/api";
import { GridContainer } from "@/components/layout/GridContainer";
import { ChatContextProvider } from "@/lib/chat-context";
import { routes } from "@/lib/routes";
import type { BillCalendarItem, VoteCalendarItem } from "@/types";
import {
  cn,
  formatDateParam,
  getWeekDates,
  getWeekStart,
  getWeekEnd,
  parseWeekParam,
  getResultBgColor,
  getResultLabel,
  getChamberShortName,
  truncate,
} from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

export const revalidate = 300; // 5 minutes

interface PageProps {
  searchParams: Promise<{ week?: string }>;
}

export async function generateMetadata({ searchParams }: PageProps) {
  const params = await searchParams;
  const weekDate = parseWeekParam(params.week || null);
  const weekStart = getWeekStart(weekDate);

  return {
    title: `Legislative Calendar - Week of ${weekStart.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}`,
    description: "Weekly view of congressional votes and legislative activity",
  };
}

interface CalendarDayProps {
  date: Date;
  votes: VoteCalendarItem[];
  bills: BillCalendarItem[];
  isToday: boolean;
}

function CalendarDay({ date, votes, bills, isToday }: CalendarDayProps) {
  const dayName = date.toLocaleDateString("en-US", { weekday: "short" });
  const dayNumber = date.getDate();
  const monthName = date.toLocaleDateString("en-US", { month: "short" });

  return (
    <div className="min-h-[200px] border-r border-border last:border-r-0">
      {/* Day header */}
      <div
        className={cn(
          "p-2 border-b border-border text-center",
          isToday && "border-b-2 border-b-accent"
        )}
      >
        <div className="text-xs text-muted-foreground uppercase">{dayName}</div>
        <div
          className={cn(
            "text-lg font-semibold",
            isToday ? "text-accent" : "text-foreground"
          )}
        >
          {dayNumber}
        </div>
        <div className="text-xs text-muted-foreground/60">{monthName}</div>
      </div>

      {/* Content */}
      <div className="divide-y divide-border overflow-y-auto max-h-[400px]">
        {/* Votes */}
        {votes.map((vote) => (
          <ClickableCard
            key={vote.vote_id}
            href={vote.bill ? routes.legislation.detail(vote.bill) : routes.vote.detail(vote.vote_id)}
            itemId={vote.vote_id}
            itemType="vote"
            className="block px-2 py-2.5 text-xs transition-colors hover:bg-accent/5"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-muted-foreground">
                {getChamberShortName(vote.chamber)}
              </span>
              <Badge className={cn("px-1.5", getResultBgColor(vote.result))}>
                {getResultLabel(vote.result)}
              </Badge>
            </div>
            <p className="text-foreground font-medium leading-tight">
              {truncate(vote.description, 60)}
            </p>
            {vote.bill_display_number && (
              <div className="text-accent mt-1">
                {vote.bill_display_number}
              </div>
            )}
            <div className="mt-1 text-muted-foreground">
              {vote.total_yea}Y - {vote.total_nay}N
            </div>
          </ClickableCard>
        ))}

        {/* Bills with action (no vote) */}
        {bills
          .filter(
            (bill) =>
              !votes.some((v) => v.bill === bill.bill_id)
          )
          .map((bill) => (
            <ClickableCard
              key={bill.bill_id}
              href={routes.legislation.detail(bill.bill_id)}
              itemId={bill.bill_id}
              itemType="bill"
              className="block px-2 py-2.5 text-xs transition-colors hover:bg-accent/5"
            >
              <div className="font-medium text-accent">
                {bill.display_number}
              </div>
              <p className="text-foreground/80 leading-tight mt-1">
                {truncate(bill.short_title || bill.latest_action_text, 60)}
              </p>
            </ClickableCard>
          ))}

        {/* Empty state */}
        {votes.length === 0 && bills.length === 0 && (
          <p className="text-muted-foreground/60 text-xs text-center py-4">No activity</p>
        )}
      </div>
    </div>
  );
}

export default async function CalendarPage({ searchParams }: PageProps) {
  const params = await searchParams;
  const weekDate = parseWeekParam(params.week || null);
  const weekStart = getWeekStart(weekDate);
  const weekEnd = getWeekEnd(weekDate);
  const weekDates = getWeekDates(weekDate);

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  // Fetch data for the week
  const dateFrom = formatDateParam(weekStart);
  const dateTo = formatDateParam(weekEnd);

  const [votesResponse, billsResponse] = await Promise.all([
    getVotesCalendar(dateFrom, dateTo),
    getBillsCalendar(dateFrom, dateTo),
  ]);

  // Group by date
  const votesByDate = new Map<string, VoteCalendarItem[]>();
  const billsByDate = new Map<string, BillCalendarItem[]>();

  for (const vote of votesResponse.results) {
    const dateKey = vote.date;
    if (!votesByDate.has(dateKey)) {
      votesByDate.set(dateKey, []);
    }
    votesByDate.get(dateKey)!.push(vote);
  }

  for (const bill of billsResponse.results) {
    if (bill.latest_action_date) {
      const dateKey = bill.latest_action_date;
      if (!billsByDate.has(dateKey)) {
        billsByDate.set(dateKey, []);
      }
      billsByDate.get(dateKey)!.push(bill);
    }
  }

  // Navigation links
  const prevWeek = new Date(weekStart);
  prevWeek.setDate(prevWeek.getDate() - 7);
  const nextWeek = new Date(weekStart);
  nextWeek.setDate(nextWeek.getDate() + 7);

  const formatWeekRange = (start: Date, end: Date) => {
    const startStr = start.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
    const endStr = end.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
    return `${startStr} - ${endStr}`;
  };

  return (
    <ChatContextProvider context={{ type: "calendar", data: { week_start: dateFrom, week_end: dateTo } }}>
    <main className="min-h-screen bg-background">
      <GridContainer className="py-10">
        {/* Back link */}
        <Link
          href={routes.home}
          className="cursor-pointer inline-flex items-center gap-0.5 text-sm text-muted-foreground hover:text-foreground transition-colors mb-2"
        >
          <ChevronLeft className="size-4" />
          Back
        </Link>

        {/* Header */}
        <div className="mb-8 border-b-2 border-foreground pb-5">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              Legislative Calendar
            </h1>

            {/* Week Navigation */}
            <div className="flex items-center gap-4">
              <Link
                href={routes.calendar.week(formatDateParam(prevWeek))}
                className="p-1 text-muted-foreground transition-colors hover:text-foreground"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
              </Link>

              <span className="font-medium text-foreground">
                {formatWeekRange(weekStart, weekEnd)}
              </span>

              <Link
                href={routes.calendar.week(formatDateParam(nextWeek))}
                className="p-1 text-muted-foreground transition-colors hover:text-foreground"
              >
                <svg
                  className="w-5 h-5"
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
              </Link>

              <Link
                href={routes.calendar.index}
                className="ml-2 text-sm font-medium text-accent hover:underline"
              >
                Today
              </Link>
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="mb-4 flex items-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <div className="h-3 w-0.5 bg-muted-foreground" />
            <span className="text-muted-foreground">Vote</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-0.5 bg-accent" />
            <span className="text-muted-foreground">Bill Activity</span>
          </div>
        </div>

        {/* Calendar Grid */}
        <div className="border-t border-border">
          <div className="grid grid-cols-7">
            {weekDates.map((date) => {
              const dateKey = formatDateParam(date);
              const isToday = date.getTime() === today.getTime();

              return (
                <CalendarDay
                  key={dateKey}
                  date={date}
                  votes={votesByDate.get(dateKey) || []}
                  bills={billsByDate.get(dateKey) || []}
                  isToday={isToday}
                />
              );
            })}
          </div>
        </div>

        {/* Summary Stats */}
        <div className="mt-8 border-t border-border pt-6">
          <h3 className="mb-2 text-lg font-bold text-foreground">Week at a Glance</h3>
          <div className="divide-y divide-border">
            <CalendarStatRow label="Votes This Week" value={votesResponse.results.length} />
            <CalendarStatRow label="Bills With Activity" value={billsResponse.results.length} />
            <CalendarStatRow
              label="Passed / Agreed"
              value={votesResponse.results.filter((v) => v.result === "passed" || v.result === "agreed").length}
              color="text-green-600"
            />
            <CalendarStatRow
              label="Failed / Rejected"
              value={votesResponse.results.filter((v) => v.result === "failed" || v.result === "rejected").length}
              color="text-glory-red-500"
            />
          </div>
        </div>
      </GridContainer>
    </main>
    </ChatContextProvider>
  );
}

// --- Stat row helper (matches Home page pattern) ---

function CalendarStatRow({
  label,
  value,
  color,
}: {
  label: string;
  value: number | string;
  color?: string;
}) {
  return (
    <div className="flex items-baseline justify-between py-3 last:border-b-0">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className={cn("text-xl font-bold", color || "text-foreground")}>
        {value}
      </span>
    </div>
  );
}
