import Link from "next/link";

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
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

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
    <div
      className={`min-h-[200px] border-r last:border-r-0 ${isToday ? "bg-accent/10" : "bg-card"}`}
    >
      {/* Day header */}
      <div
        className={`p-2 border-b text-center ${isToday ? "bg-accent/15" : "bg-secondary"}`}
      >
        <div className="text-xs text-muted-foreground uppercase">{dayName}</div>
        <div
          className={`text-lg font-semibold ${isToday ? "text-accent" : "text-foreground"}`}
        >
          {dayNumber}
        </div>
        <div className="text-xs text-muted-foreground/60">{monthName}</div>
      </div>

      {/* Content */}
      <div className="p-2 space-y-2 overflow-y-auto max-h-[400px]">
        {/* Votes */}
        {votes.map((vote) => (
          <ClickableCard
            key={vote.vote_id}
            href={vote.bill ? routes.legislation.detail(vote.bill) : routes.vote.detail(vote.vote_id)}
            itemId={vote.vote_id}
            itemType="vote"
            className="block p-2 rounded bg-gradient-to-r from-secondary to-secondary/50 border-l-4 border-muted-foreground text-xs hover:from-muted hover:to-secondary transition-colors"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-muted-foreground">
                {getChamberShortName(vote.chamber)}
              </span>
              <Badge className={cn("px-1.5", getResultBgColor(vote.result))}>
                {getResultLabel(vote.result)}
              </Badge>
            </div>
            <p className="text-foreground/80 font-medium leading-tight">
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
              className="block p-2 bg-accent/10 border-l-4 border-accent text-xs hover:bg-accent/20 transition-colors"
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
      <GridContainer className="py-6">
        {/* Header */}
        <Card className="p-4 py-4 mb-6">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-foreground">
              Legislative Calendar
            </h1>

            {/* Week Navigation */}
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="icon" asChild>
              <Link
                href={routes.calendar.week(formatDateParam(prevWeek))}
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
              </Button>

              <div className="text-center">
                <span className="font-medium text-foreground">
                  {formatWeekRange(weekStart, weekEnd)}
                </span>
              </div>

              <Button variant="ghost" size="icon" asChild>
              <Link
                href={routes.calendar.week(formatDateParam(nextWeek))}
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
              </Button>

              <Button variant="outline" size="sm" className="ml-2" asChild>
                <Link href={routes.calendar.index}>
                  Today
                </Link>
              </Button>
            </div>
          </div>
        </Card>

        {/* Legend */}
        <Card className="p-3 py-3 mb-4">
          <div className="flex items-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 border-l-4 border-muted-foreground bg-secondary" />
              <span className="text-muted-foreground">Vote</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 border-l-4 border-accent bg-accent/10" />
              <span className="text-muted-foreground">Bill Activity</span>
            </div>
          </div>
        </Card>

        {/* Calendar Grid */}
        <Card className="overflow-hidden p-0 py-0">
          <div className="grid grid-cols-7 divide-x border-b">
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
        </Card>

        {/* Summary Stats */}
        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="p-4 py-4 text-center">
            <p className="text-3xl font-bold text-foreground">
              {votesResponse.results.length}
            </p>
            <p className="text-sm text-muted-foreground">Votes This Week</p>
          </Card>
          <Card className="p-4 py-4 text-center">
            <p className="text-3xl font-bold text-foreground">
              {billsResponse.results.length}
            </p>
            <p className="text-sm text-muted-foreground">Bills With Activity</p>
          </Card>
          <Card className="p-4 py-4 text-center">
            <p className="text-3xl font-bold text-green-600">
              {votesResponse.results.filter((v) => v.result === "passed" || v.result === "agreed").length}
            </p>
            <p className="text-sm text-muted-foreground">Passed/Agreed</p>
          </Card>
          <Card className="p-4 py-4 text-center">
            <p className="text-3xl font-bold text-red-600">
              {votesResponse.results.filter((v) => v.result === "failed" || v.result === "rejected").length}
            </p>
            <p className="text-sm text-muted-foreground">Failed/Rejected</p>
          </Card>
        </div>
      </GridContainer>
    </main>
    </ChatContextProvider>
  );
}
