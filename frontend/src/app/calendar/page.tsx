import Link from "next/link";
import { ChevronLeft, ChevronRight } from "lucide-react";

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
import { CalendarDayPicker } from "./CalendarDayPicker";

export const revalidate = 300;

interface PageProps {
  searchParams: Promise<{ week?: string; day?: string }>;
}

export async function generateMetadata({ searchParams }: PageProps) {
  const params = await searchParams;
  const weekDate = parseWeekParam(params.week || null);
  const weekStart = getWeekStart(weekDate);
  const title = `Legislative Calendar - Week of ${weekStart.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}`;
  const description =
    "Weekly view of congressional votes and legislative activity";

  return {
    title,
    description,
    alternates: { canonical: "/calendar" },
    openGraph: { title, description, url: "/calendar" },
    twitter: { card: "summary" as const, title, description },
  };
}

// --- Day column ---

interface CalendarDayProps {
  date: Date;
  votes: VoteCalendarItem[];
  bills: BillCalendarItem[];
  isToday: boolean;
}

function CalendarDay({ date, votes, bills, isToday }: CalendarDayProps) {
  const dayName = date.toLocaleDateString("en-US", { weekday: "short" }).toUpperCase();
  const dayNumber = date.getDate();

  const filteredBills = bills.filter(
    (bill) => !votes.some((v) => v.bill === bill.bill_id)
  );

  const hasActivity = votes.length > 0 || filteredBills.length > 0;

  return (
    <div className="flex flex-col">
      {/* Day header */}
      <div className="flex flex-col items-center py-2">
        <span className="text-[11px] font-medium text-muted-foreground tracking-wide">
          {dayName}
        </span>
        <span
          className={cn(
            "mt-0.5 flex size-8 items-center justify-center rounded-full text-sm font-semibold",
            isToday
              ? "bg-accent text-white"
              : "text-foreground"
          )}
        >
          {dayNumber}
        </span>
      </div>

      {/* Events */}
      <div className="flex-1 border-t border-border px-1 py-1 space-y-1 overflow-y-auto max-h-[650px]">
        {votes.map((vote) => (
          <Link
            key={vote.vote_id}
            href={
              vote.bill
                ? routes.legislation.detail(vote.bill)
                : routes.vote.detail(vote.vote_id)
            }
            className="cursor-pointer block rounded-lg bg-secondary/50 px-2 py-2 text-xs transition-colors hover:bg-secondary"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-muted-foreground text-[11px]">
                {getChamberShortName(vote.chamber)}
              </span>
              <Badge
                className={cn(
                  "px-1.5 py-0 text-[10px]",
                  getResultBgColor(vote.result)
                )}
              >
                {getResultLabel(vote.result)}
              </Badge>
            </div>
            <p className="text-foreground font-medium leading-tight text-[12px]">
              {truncate(vote.description, 80)}
            </p>
            {vote.bill_display_number && (
              <div className="text-accent text-[11px] mt-1">
                {vote.bill_display_number}
              </div>
            )}
            <div className="mt-1 text-muted-foreground text-[11px]">
              {vote.total_yea}Y - {vote.total_nay}N
            </div>
          </Link>
        ))}

        {filteredBills.map((bill) => (
          <Link
            key={bill.bill_id}
            href={routes.legislation.detail(bill.bill_id)}
            className="cursor-pointer block rounded-lg bg-accent/5 px-2 py-2 text-xs transition-colors hover:bg-accent/10"
          >
            <div className="font-medium text-accent text-[12px]">
              {bill.display_number}
            </div>
            <p className="text-foreground/80 leading-tight mt-0.5 text-[11px]">
              {truncate(bill.short_title || bill.latest_action_text, 80)}
            </p>
          </Link>
        ))}

        {!hasActivity && (
          <p className="text-muted-foreground/40 text-[11px] text-center py-6">
            No activity
          </p>
        )}
      </div>
    </div>
  );
}

// --- Main page ---

export default async function CalendarPage({ searchParams }: PageProps) {
  const params = await searchParams;
  const weekDate = parseWeekParam(params.week || null);
  const weekStart = getWeekStart(weekDate);
  const weekEnd = getWeekEnd(weekDate);
  const weekDates = getWeekDates(weekDate);

  const today = new Date();
  today.setHours(0, 0, 0, 0);

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
    if (!votesByDate.has(dateKey)) votesByDate.set(dateKey, []);
    votesByDate.get(dateKey)!.push(vote);
  }

  for (const bill of billsResponse.results) {
    if (bill.latest_action_date) {
      const dateKey = bill.latest_action_date;
      if (!billsByDate.has(dateKey)) billsByDate.set(dateKey, []);
      billsByDate.get(dateKey)!.push(bill);
    }
  }

  // Navigation
  const prevWeek = new Date(weekStart);
  prevWeek.setDate(prevWeek.getDate() - 7);
  const nextWeek = new Date(weekStart);
  nextWeek.setDate(nextWeek.getDate() + 7);

  const monthYear = weekStart.toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });

  // Stats
  const passedAgreed = votesResponse.results.filter(
    (v) => v.result === "passed" || v.result === "agreed"
  ).length;
  const failedRejected = votesResponse.results.filter(
    (v) => v.result === "failed" || v.result === "rejected"
  ).length;

  return (
    <ChatContextProvider
      context={{ type: "calendar", data: { week_start: dateFrom, week_end: dateTo } }}
    >
      <main className="min-h-screen bg-background">
        <GridContainer className="py-10">
          {/* Back link */}
          <Link
            href={routes.home}
            className="cursor-pointer inline-flex items-center gap-0.5 text-sm text-muted-foreground hover:text-foreground transition-colors mb-4"
          >
            <ChevronLeft className="size-4" />
            Back
          </Link>

          {/* Apple Calendar-style header */}
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-bold text-foreground sm:text-3xl">
              {monthYear}
            </h1>

            <div className="flex items-center gap-2">
              <Link
                href={routes.calendar.index}
                className="cursor-pointer rounded-lg border border-border px-3 py-1.5 text-sm font-medium text-foreground hover:bg-secondary transition-colors"
              >
                Today
              </Link>
              <div className="flex items-center">
                <Link
                  href={routes.calendar.week(formatDateParam(prevWeek))}
                  className="cursor-pointer rounded-l-lg border border-border p-1.5 text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
                >
                  <ChevronLeft className="size-4" />
                </Link>
                <Link
                  href={routes.calendar.week(formatDateParam(nextWeek))}
                  className="cursor-pointer rounded-r-lg border border-border border-l-0 p-1.5 text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
                >
                  <ChevronRight className="size-4" />
                </Link>
              </div>
            </div>
          </div>

          {/* Mobile day picker */}
          <div className="sm:hidden mb-4">
            <CalendarDayPicker
              weekDates={weekDates.map((d) => formatDateParam(d))}
              today={formatDateParam(today)}
              weekParam={params.week || null}
            />
          </div>

          {/* Desktop: 7-column week grid */}
          <div className="hidden sm:grid sm:grid-cols-7 sm:divide-x sm:divide-border sm:border sm:border-border sm:rounded-xl sm:bg-card sm:overflow-hidden">
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

          {/* Mobile: single day view */}
          <div className="sm:hidden">
            <MobileDayView
              weekDates={weekDates}
              today={today}
              selectedDay={params.day || null}
              votesByDate={votesByDate}
              billsByDate={billsByDate}
            />
          </div>

          {/* Week Stats */}
          <div className="mt-8 border-t border-border pt-6">
            <h3 className="mb-2 text-lg font-bold text-foreground">
              Week at a Glance
            </h3>
            <div className="divide-y divide-border">
              <StatRow label="Votes This Week" value={votesResponse.results.length} />
              <StatRow label="Bills With Activity" value={billsResponse.results.length} />
              <StatRow label="Passed / Agreed" value={passedAgreed} color="text-green-600" />
              <StatRow label="Failed / Rejected" value={failedRejected} color="text-glory-red-500" />
            </div>
          </div>
        </GridContainer>
      </main>
    </ChatContextProvider>
  );
}

// --- Mobile day view ---

function MobileDayView({
  weekDates,
  today,
  selectedDay,
  votesByDate,
  billsByDate,
}: {
  weekDates: Date[];
  today: Date;
  selectedDay: string | null;
  votesByDate: Map<string, VoteCalendarItem[]>;
  billsByDate: Map<string, BillCalendarItem[]>;
}) {
  // Default to today if it's in the week, otherwise the first day
  const todayStr = formatDateParam(today);
  const weekDateStrs = weekDates.map((d) => formatDateParam(d));

  let activeDateStr = selectedDay;
  if (!activeDateStr || !weekDateStrs.includes(activeDateStr)) {
    activeDateStr = weekDateStrs.includes(todayStr)
      ? todayStr
      : weekDateStrs[0];
  }

  const activeDate = weekDates.find(
    (d) => formatDateParam(d) === activeDateStr
  )!;
  const isToday = activeDate.getTime() === today.getTime();

  return (
    <div className="border border-border rounded-xl bg-card overflow-hidden">
      <CalendarDay
        date={activeDate}
        votes={votesByDate.get(activeDateStr) || []}
        bills={billsByDate.get(activeDateStr) || []}
        isToday={isToday}
      />
    </div>
  );
}

// --- Stat row ---

function StatRow({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
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
