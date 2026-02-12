import Link from "next/link";

import { getCurrentWeeklySummaries } from "@/lib/api";
import { GridContainer } from "@/components/layout/GridContainer";
import { routes } from "@/lib/routes";
import { cn, formatDateLong } from "@/lib/utils";
import type { WeeklySummary } from "@/types";
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

export const revalidate = 900; // 15 minutes

export const metadata = {
  title: "This Week in Congress",
  description:
    "Weekly recap and preview of congressional activity, bills, and votes",
};

interface SummaryCardProps {
  summary: WeeklySummary;
  type: "recap" | "preview";
}

function SummaryCard({ summary, type }: SummaryCardProps) {
  const isRecap = type === "recap";

  return (
    <Card
      className={cn("overflow-hidden border-t-4 gap-0 py-0", isRecap ? "border-blue-500" : "border-green-500")}
    >
      {/* Header */}
      <CardHeader
        className={cn("py-4", isRecap ? "bg-blue-50" : "bg-green-50")}
      >
        <div className="flex items-center justify-between">
          <div>
            <CardTitle
              className={cn("text-xl", isRecap ? "text-blue-900" : "text-green-900")}
            >
              {summary.summary_type_display}
            </CardTitle>
            <CardDescription className="mt-1">
              Week {summary.week_number}, {summary.year}
            </CardDescription>
          </div>
          <div
            className={`p-3 rounded-full ${
              isRecap ? "bg-blue-100" : "bg-green-100"
            }`}
          >
            {isRecap ? (
              <svg
                className="w-6 h-6 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
                />
              </svg>
            ) : (
              <svg
                className="w-6 h-6 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
            )}
          </div>
        </div>
      </CardHeader>

      {/* Content */}
      <CardContent className="py-5">
        <div className="prose prose-sm max-w-none text-foreground/80 whitespace-pre-wrap">
          {summary.content}
        </div>
      </CardContent>

      {/* Footer with stats */}
      <CardFooter className="py-4 bg-secondary border-t">
        <div className="flex w-full items-center justify-between text-sm text-muted-foreground">
          <div className="flex items-center gap-4">
            {summary.votes_included.length > 0 && (
              <span>{summary.votes_included.length} votes included</span>
            )}
            {summary.bills_included.length > 0 && (
              <span>{summary.bills_included.length} bills referenced</span>
            )}
          </div>
          <time dateTime={summary.created_at}>
            Updated {formatDateLong(summary.created_at)}
          </time>
        </div>
      </CardFooter>
    </Card>
  );
}

function EmptyState() {
  return (
    <Card className="p-8 py-8 text-center">
      <div className="mx-auto w-16 h-16 rounded-full bg-background flex items-center justify-center mb-4">
        <svg
          className="w-8 h-8 text-muted-foreground/60"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </div>
      <h3 className="text-lg font-medium text-foreground mb-2">
        No Summaries Yet
      </h3>
      <p className="text-muted-foreground max-w-md mx-auto">
        Weekly summaries are generated automatically. Check back on Saturday for
        the weekly recap and Sunday for the week ahead preview.
      </p>
    </Card>
  );
}

export default async function ThisWeekPage() {
  const summaries = await getCurrentWeeklySummaries();

  const recap = summaries.find((s) => s.summary_type === "recap");
  const preview = summaries.find((s) => s.summary_type === "preview");

  const currentWeek = recap?.week_number || preview?.week_number;
  const currentYear = recap?.year || preview?.year;

  return (
    <main className="min-h-screen bg-background">
      <GridContainer className="py-6">
        {/* Header */}
        <Card className="p-6 py-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-foreground">
                This Week in Congress
              </h1>
              {currentWeek && currentYear && (
                <p className="text-muted-foreground mt-1">
                  Week {currentWeek}, {currentYear}
                </p>
              )}
            </div>
            <Button variant="outline" asChild>
            <Link href={routes.calendar.index}>
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
                  d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
              Full Calendar
            </Link>
            </Button>
          </div>
        </Card>

        {/* Summaries */}
        {summaries.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="space-y-6">
            {/* Week in Review (Recap) */}
            {recap && <SummaryCard summary={recap} type="recap" />}

            {/* Week Ahead (Preview) */}
            {preview && <SummaryCard summary={preview} type="preview" />}
          </div>
        )}

        {/* Info banner */}
        <Alert className="mt-8 border-accent/20 bg-accent/10">
          <svg
            className="h-5 w-5 text-accent"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <AlertTitle className="text-accent">About these summaries</AlertTitle>
          <AlertDescription className="text-accent/80">
            These AI-generated summaries provide a nonpartisan overview of
            congressional activity. The Week in Review is published on Saturday
            mornings, and the Week Ahead preview is published on Sunday evenings.
          </AlertDescription>
        </Alert>
      </GridContainer>
    </main>
  );
}
