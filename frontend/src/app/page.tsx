import Link from "next/link";

import {
  getCurrentWeeklySummaries,
  getVotesCalendar,
  getBillsCalendar,
  getSeats,
} from "@/lib/api";
import { GridContainer } from "@/components/layout/GridContainer";
import { ChatContextProvider } from "@/lib/chat-context";
import { routes } from "@/lib/routes";
import type { BillCalendarItem, VoteCalendarItem } from "@/types";
import {
  cn,
  formatDateLong,
  formatDateParam,
  formatRelativeTime,
  generateBillHeadline,
  generateVoteHeadline,
  getResultBgColor,
  getResultLabel,
  getChamberShortName,
  getWeekStart,
  getWeekEnd,
  truncate,
} from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import FindYourRep from "@/components/home/FindYourRep";
import MiniHemicycle from "@/components/home/MiniHemicycle";
import YourRepsThisWeek from "@/components/home/YourRepsThisWeek";

export const revalidate = 300; // 5 minutes

export const metadata = {
  title: "OpenCongress - Congressional Activity Tracker",
  description:
    "Track congressional activity, explore legislation, and follow your representatives with real-time updates and AI-generated summaries.",
  alternates: { canonical: "/" },
  openGraph: {
    title: "OpenCongress - Congressional Activity Tracker",
    description:
      "Track congressional activity, explore legislation, and follow your representatives.",
    url: "/",
  },
  twitter: {
    card: "summary_large_image" as const,
    title: "OpenCongress",
    description:
      "Track congressional activity, explore legislation, and follow your representatives.",
  },
};

// --- Activity feed types ---

type ActivityItem =
  | { type: "vote"; data: VoteCalendarItem; date: string; headline: string }
  | { type: "bill"; data: BillCalendarItem; date: string; headline: string };

// --- Page ---

export default async function Home() {
  const now = new Date();
  const weekStart = getWeekStart(now);
  const weekEnd = getWeekEnd(now);
  const dateFrom = formatDateParam(weekStart);
  const dateTo = formatDateParam(weekEnd);

  const [summaries, votesResponse, billsResponse, senateSeats] =
    await Promise.all([
      getCurrentWeeklySummaries(),
      getVotesCalendar(dateFrom, dateTo),
      getBillsCalendar(dateFrom, dateTo),
      getSeats("senate"),
    ]);

  const recap = summaries.find((s) => s.summary_type === "recap");
  const preview = summaries.find((s) => s.summary_type === "preview");

  const votes = votesResponse.results;
  const bills = billsResponse.results;

  // --- Stats ---
  const passedAgreed = votes.filter(
    (v) => v.result === "passed" || v.result === "agreed"
  ).length;
  const failedRejected = votes.filter(
    (v) => v.result === "failed" || v.result === "rejected"
  ).length;
  const bipartisanCount = votes.filter((v) => v.is_bipartisan).length;
  const bipartisanPercent =
    votes.length > 0 ? Math.round((bipartisanCount / votes.length) * 100) : 0;
  const closestVote =
    votes.length > 0
      ? votes.reduce((closest, vote) => {
          const margin = Math.abs(vote.total_yea - vote.total_nay);
          const closestMargin = Math.abs(
            closest.total_yea - closest.total_nay
          );
          return margin < closestMargin ? vote : closest;
        })
      : null;

  // --- Activity feed ---
  const voteIds = new Set(votes.map((v) => v.bill).filter(Boolean));
  const activityItems: ActivityItem[] = [
    ...votes.map((vote) => ({
      type: "vote" as const,
      data: vote,
      date: vote.date,
      headline: generateVoteHeadline(vote),
    })),
    ...bills
      .filter((bill) => !voteIds.has(bill.bill_id))
      .map((bill) => ({
        type: "bill" as const,
        data: bill,
        date: bill.latest_action_date || "",
        headline: generateBillHeadline(bill),
      })),
  ];
  activityItems.sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  );
  const latestActivity = activityItems.slice(0, 6);

  // --- Excerpt helper ---
  function extractExcerpt(text: string, sentences: number = 3): string {
    // Strip markdown bold/italic markers and skip title lines
    const cleaned = text
      .replace(/\*\*[^*]+\*\*\s*/g, "") // remove **bold** blocks (title lines)
      .replace(/\*([^*]+)\*/g, "$1") // convert *italic* to plain
      .replace(/#{1,6}\s+/g, "") // remove markdown headers
      .trim();
    const parts = cleaned.split(/(?<=\.)\s+/);
    const excerpt = parts.slice(0, sentences).join(" ");
    return parts.length > sentences ? excerpt + " ..." : excerpt;
  }

  return (
    <ChatContextProvider
      context={{
        type: "home",
        data: {
          week_summary: recap?.content?.slice(0, 500) || "",
          total_votes: votes.length,
          total_bills: bills.length,
        },
      }}
    >
      <main className="min-h-screen bg-background">
        <GridContainer className="py-10">
          {/* Date header */}
          <div className="mb-10 border-b-2 border-foreground pb-5">
              <time className="text-sm uppercase tracking-widest text-muted-foreground">
                {formatDateLong(formatDateParam(now))}
              </time>
              <h1 className="mt-1 text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
                OpenCongress
              </h1>
          </div>

          {/* Main grid: 8 + 4 columns on large screens */}
          <div className="grid grid-cols-1 gap-10 lg:grid-cols-12 lg:gap-12">
            {/* ============ LEFT COLUMN ============ */}
            <div className="flex flex-col gap-10 lg:col-span-8">
              {/* Lead Story: Week in Review */}
              <div className="border-b border-border pb-10">
                <h2 className="font-domine text-2xl font-bold text-foreground sm:text-3xl">
                  {recap?.summary_type_display || "Week in Review"}
                </h2>
                {votes.length > 0 && (
                  <p className="mt-1 text-base text-muted-foreground">
                    {votes.length} vote{votes.length !== 1 ? "s" : ""},{" "}
                    {bills.length} bill{bills.length !== 1 ? "s" : ""} this
                    week
                  </p>
                )}
                <div className="mt-6 flex flex-col gap-8 md:flex-row md:items-start">
                  {/* Left: text */}
                  <div className="space-y-4 md:w-2/5">
                    {recap ? (
                      <p className="font-domine font-medium leading-relaxed text-foreground/80">
                        {extractExcerpt(recap.content, 3)}
                      </p>
                    ) : (
                      <p className="text-muted-foreground">
                        Weekly summaries are generated automatically. Check back
                        on Saturday for the weekly recap.
                      </p>
                    )}
                    <Link
                      href={routes.thisWeek.index}
                      className="inline-flex cursor-pointer items-center gap-1 font-semibold text-accent hover:underline"
                    >
                      Read Full Summary →
                    </Link>
                  </div>
                  {/* Right: hemicycle */}
                  {senateSeats.length > 0 && (
                    <div className="w-full md:flex-1">
                      <MiniHemicycle seats={senateSeats} />
                    </div>
                  )}
                </div>
              </div>

              {/* Latest Activity Feed */}
              <div>
                <h2 className="mb-4 text-xl font-bold text-foreground">
                  Latest Activity
                </h2>
                {latestActivity.length > 0 ? (
                  <div className="divide-y divide-border border-y border-border">
                    {latestActivity.map((item) => {
                      const key =
                        item.type === "vote"
                          ? item.data.vote_id
                          : item.data.bill_id;
                      const href =
                        item.type === "vote"
                          ? item.data.bill
                            ? routes.legislation.detail(item.data.bill)
                            : routes.vote.detail(item.data.vote_id)
                          : routes.legislation.detail(item.data.bill_id);

                      return (
                        <Link
                          key={key}
                          href={href}
                          className="flex cursor-pointer items-start justify-between gap-4 p-4 transition-colors hover:bg-accent/5"
                        >
                          <div className="min-w-0 flex-1">
                            <div className="mb-1 flex flex-wrap items-center gap-2">
                              <Badge variant="outline" className="text-xs">
                                {item.type === "vote" ? "Vote" : "Bill"}
                              </Badge>
                              {item.type === "vote" && (
                                <>
                                  <Badge variant="secondary" className="text-xs">
                                    {getChamberShortName(item.data.chamber)}
                                  </Badge>
                                  <Badge
                                    className={cn(
                                      "text-xs",
                                      getResultBgColor(item.data.result)
                                    )}
                                  >
                                    {getResultLabel(item.data.result)}
                                  </Badge>
                                  {item.data.is_bipartisan && (
                                    <Badge variant="outline" className="text-xs border-violet-400 text-violet-600">
                                      Bipartisan
                                    </Badge>
                                  )}
                                </>
                              )}
                            </div>
                            <h3 className="font-semibold leading-snug text-foreground">
                              {item.headline}
                            </h3>
                          </div>
                          <time className="shrink-0 text-xs text-muted-foreground">
                            {formatRelativeTime(item.date)}
                          </time>
                        </Link>
                      );
                    })}
                  </div>
                ) : (
                  <p className="py-6 text-center text-muted-foreground">
                    No activity this week yet.
                  </p>
                )}
                <div className="mt-3 text-right">
                  <Link
                    href={routes.calendar.index}
                    className="cursor-pointer text-sm font-medium text-accent hover:underline"
                  >
                    View Full Calendar →
                  </Link>
                </div>
              </div>
            </div>

            {/* ============ RIGHT COLUMN (sidebar) ============ */}
            <div className="flex flex-col divide-y divide-border lg:col-span-4 lg:border-l lg:border-border lg:pl-10">
              {/* Your Reps This Week (personalized, client component) */}
              <YourRepsThisWeek />

              {/* Week by the Numbers */}
              <div className="pb-10">
                <h3 className="text-lg font-bold text-foreground">
                  Week by the Numbers
                </h3>
                <div>
                  <StatRow label="Total Votes" value={votes.length} />
                  <StatRow label="Bills with Activity" value={bills.length} />
                  <StatRow
                    label="Passed / Agreed"
                    value={passedAgreed}
                    color="text-green-600"
                  />
                  <StatRow
                    label="Failed / Rejected"
                    value={failedRejected}
                    color="text-glory-red-500"
                  />
                  <StatRow
                    label="Bipartisan Votes"
                    value={`${bipartisanPercent}%`}
                  />
                  {closestVote && (
                    <div className="border-t border-border px-0 py-3">
                      <p className="text-xs text-muted-foreground">
                        Closest Vote
                      </p>
                      <Link
                        href={
                          closestVote.bill
                            ? routes.legislation.detail(closestVote.bill)
                            : routes.vote.detail(closestVote.vote_id)
                        }
                        className="cursor-pointer text-sm font-medium text-foreground hover:text-accent"
                      >
                        {truncate(closestVote.description, 50)}
                      </Link>
                      <p className="mt-0.5 text-xs text-muted-foreground">
                        {closestVote.total_yea}-{closestVote.total_nay} (margin:{" "}
                        {Math.abs(
                          closestVote.total_yea - closestVote.total_nay
                        )}
                        )
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Find Your Rep */}
              <div className="py-10">
                <h3 className="text-lg font-bold text-foreground">
                  Find Your Representative
                </h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  Enter your zip code to find your members of Congress
                </p>
                <div className="mt-3">
                  <FindYourRep />
                </div>
              </div>

              {/* Week Ahead */}
              <div className="border-l-4 border-green-500 pl-4 pt-10">
                <h3 className="font-domine text-lg font-bold text-foreground">
                  {preview?.summary_type_display || "Week Ahead"}
                </h3>
                <div className="mt-3">
                  {preview ? (
                    <>
                      <p className="mb-4 font-domine font-medium text-sm leading-relaxed text-foreground/80">
                        {extractExcerpt(preview.content, 2)}
                      </p>
                      <Link
                        href={routes.thisWeek.index}
                        className="inline-flex cursor-pointer items-center gap-1 text-sm font-semibold text-accent hover:underline"
                      >
                        Read Full Preview →
                      </Link>
                    </>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      Week ahead preview will be available Sunday evening.
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Quick Links */}
          <nav className="mt-12 border-t border-border pt-8">
            <div className="flex flex-wrap items-center justify-center gap-6">
              <Link
                href={routes.senate.index}
                className="cursor-pointer text-sm font-medium text-foreground hover:text-accent"
              >
                Senate
              </Link>
              <span className="text-muted-foreground">·</span>
              <Link
                href={routes.house.index}
                className="cursor-pointer text-sm font-medium text-foreground hover:text-accent"
              >
                House
              </Link>
              <span className="text-muted-foreground">·</span>
              <Link
                href={routes.calendar.index}
                className="cursor-pointer text-sm font-medium text-foreground hover:text-accent"
              >
                Calendar
              </Link>
              <span className="text-muted-foreground">·</span>
              <Link
                href={routes.thisWeek.index}
                className="cursor-pointer text-sm font-medium text-foreground hover:text-accent"
              >
                This Week
              </Link>
              <span className="text-muted-foreground">·</span>
              <Link
                href={routes.documentation.index}
                className="cursor-pointer text-sm font-medium text-foreground hover:text-accent"
              >
                Documentation
              </Link>
            </div>
            <p className="mt-4 text-center text-xs text-muted-foreground">
              Making congressional data accessible and transparent.
            </p>
          </nav>
        </GridContainer>
      </main>
    </ChatContextProvider>
  );
}

// --- Stat row helper ---

function StatRow({
  label,
  value,
  color,
}: {
  label: string;
  value: number | string;
  color?: string;
}) {
  return (
    <div className="flex items-baseline justify-between border-b border-border py-3 last:border-b-0">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className={cn("text-xl font-bold", color || "text-foreground")}>
        {value}
      </span>
    </div>
  );
}
