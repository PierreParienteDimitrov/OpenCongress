import Link from "next/link";

import { getBillsCalendar, getVotesCalendar } from "@/lib/api";
import { routes } from "@/lib/routes";
import type { BillCalendarItem, VoteCalendarItem } from "@/types";
import {
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
      className={`min-h-[200px] border-r last:border-r-0 ${isToday ? "bg-blue-50" : "bg-white"}`}
    >
      {/* Day header */}
      <div
        className={`p-2 border-b text-center ${isToday ? "bg-blue-100" : "bg-gray-50"}`}
      >
        <div className="text-xs text-gray-500 uppercase">{dayName}</div>
        <div
          className={`text-lg font-semibold ${isToday ? "text-blue-600" : "text-gray-900"}`}
        >
          {dayNumber}
        </div>
        <div className="text-xs text-gray-400">{monthName}</div>
      </div>

      {/* Content */}
      <div className="p-2 space-y-2 overflow-y-auto max-h-[400px]">
        {/* Votes */}
        {votes.map((vote) => (
          <div
            key={vote.vote_id}
            className="p-2 rounded bg-gradient-to-r from-gray-100 to-gray-50 border-l-4 border-gray-400 text-xs"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-gray-500">
                {getChamberShortName(vote.chamber)}
              </span>
              <span
                className={`px-1.5 py-0.5 rounded text-xs ${getResultBgColor(vote.result)}`}
              >
                {getResultLabel(vote.result)}
              </span>
            </div>
            <p className="text-gray-700 font-medium leading-tight">
              {truncate(vote.description, 60)}
            </p>
            {vote.bill && (
              <Link
                href={routes.legislation.detail(vote.bill)}
                className="text-blue-600 hover:text-blue-800 mt-1 inline-block"
              >
                {vote.bill_display_number}
              </Link>
            )}
            <div className="mt-1 text-gray-500">
              {vote.total_yea}Y - {vote.total_nay}N
            </div>
          </div>
        ))}

        {/* Bills with action (no vote) */}
        {bills
          .filter(
            (bill) =>
              !votes.some((v) => v.bill === bill.bill_id)
          )
          .map((bill) => (
            <Link
              key={bill.bill_id}
              href={routes.legislation.detail(bill.bill_id)}
              className="block p-2 rounded bg-gradient-to-r from-amber-50 to-amber-100/50 border-l-4 border-amber-400 text-xs hover:bg-amber-100 transition-colors"
            >
              <div className="font-medium text-amber-800">
                {bill.display_number}
              </div>
              <p className="text-gray-700 leading-tight mt-1">
                {truncate(bill.short_title || bill.latest_action_text, 60)}
              </p>
            </Link>
          ))}

        {/* Empty state */}
        {votes.length === 0 && bills.length === 0 && (
          <p className="text-gray-400 text-xs text-center py-4">No activity</p>
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
    <main className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">
              Legislative Calendar
            </h1>

            {/* Week Navigation */}
            <div className="flex items-center gap-4">
              <Link
                href={routes.calendar.week(formatDateParam(prevWeek))}
                className="p-2 rounded-lg hover:bg-gray-100 text-gray-600 transition-colors"
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

              <div className="text-center">
                <span className="font-medium text-gray-900">
                  {formatWeekRange(weekStart, weekEnd)}
                </span>
              </div>

              <Link
                href={routes.calendar.week(formatDateParam(nextWeek))}
                className="p-2 rounded-lg hover:bg-gray-100 text-gray-600 transition-colors"
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
                className="ml-2 px-3 py-1 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Today
              </Link>
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="bg-white rounded-lg shadow-sm p-3 mb-4">
          <div className="flex items-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded border-l-4 border-gray-400 bg-gray-100" />
              <span className="text-gray-600">Vote</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded border-l-4 border-amber-400 bg-amber-50" />
              <span className="text-gray-600">Bill Activity</span>
            </div>
          </div>
        </div>

        {/* Calendar Grid */}
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
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
        </div>

        {/* Summary Stats */}
        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow-sm p-4 text-center">
            <p className="text-3xl font-bold text-gray-900">
              {votesResponse.results.length}
            </p>
            <p className="text-sm text-gray-500">Votes This Week</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-4 text-center">
            <p className="text-3xl font-bold text-gray-900">
              {billsResponse.results.length}
            </p>
            <p className="text-sm text-gray-500">Bills With Activity</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-4 text-center">
            <p className="text-3xl font-bold text-green-600">
              {votesResponse.results.filter((v) => v.result === "passed" || v.result === "agreed").length}
            </p>
            <p className="text-sm text-gray-500">Passed/Agreed</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-4 text-center">
            <p className="text-3xl font-bold text-red-600">
              {votesResponse.results.filter((v) => v.result === "failed" || v.result === "rejected").length}
            </p>
            <p className="text-sm text-gray-500">Failed/Rejected</p>
          </div>
        </div>
      </div>
    </main>
  );
}
