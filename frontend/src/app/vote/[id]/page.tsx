import { Fragment } from "react";
import { notFound } from "next/navigation";
import Link from "next/link";
import { ChevronLeft } from "lucide-react";

import { getVote, getSeatVoteOverlay } from "@/lib/api";
import { GridContainer } from "@/components/layout/GridContainer";
import { ChatContextProvider } from "@/lib/chat-context";
import { routes } from "@/lib/routes";
import type { SeatWithVote } from "@/types";
import {
  formatDate,
  getChamberName,
  getChamberShortName,
} from "@/lib/utils";
import VoteDetailContent from "@/components/vote/VoteDetailContent";
import { Separator } from "@/components/ui/separator";

export const revalidate = 86400; // 24 hours

interface PageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: PageProps) {
  const { id } = await params;
  try {
    const vote = await getVote(id);
    const billLabel = vote.bill_short_title || vote.bill_display_number;
    const title = billLabel
      ? `${vote.question}: ${billLabel} - ${getChamberName(vote.chamber)} Vote`
      : `${vote.question} - ${getChamberName(vote.chamber)} Vote`;
    const description = vote.ai_summary
      || `${vote.total_yea} Yea, ${vote.total_nay} Nay`;
    return {
      title,
      description,
      alternates: { canonical: `/vote/${id}` },
      openGraph: {
        title,
        description,
        url: `/vote/${id}`,
      },
      twitter: {
        card: "summary",
        title,
        description,
      },
    };
  } catch {
    return {
      title: "Vote Not Found",
    };
  }
}

export default async function VotePage({ params }: PageProps) {
  const { id } = await params;

  let vote;
  try {
    vote = await getVote(id);
  } catch {
    notFound();
  }

  let overlaySeats: SeatWithVote[];
  try {
    overlaySeats = await getSeatVoteOverlay(vote.chamber, vote.vote_id);
  } catch {
    overlaySeats = [];
  }

  /* Left-column metadata — rendered on server, passed into client tabs */
  const sidebar = (
    <div className="space-y-5">
      {/* Chamber */}
      <div>
        <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
          Chamber
        </h3>
        <p className="text-sm font-medium">{getChamberName(vote.chamber)}</p>
      </div>

      {/* Date */}
      <div>
        <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
          Date
        </h3>
        <p className="text-sm font-medium">
          {formatDate(vote.date)}
          {vote.time && (
            <span className="text-muted-foreground font-normal"> · {vote.time}</span>
          )}
        </p>
      </div>

      <Separator />

      {/* Related Bill */}
      {vote.bill_display_number && (
        <Fragment key="related-bill">
          <div>
            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
              Related Bill
            </h3>
            <Link
              href={routes.legislation.detail(vote.bill_id!)}
              className="cursor-pointer text-accent hover:text-accent/80 text-sm font-medium"
            >
              {vote.bill_display_number}
            </Link>
            {vote.bill_short_title && (
              <p className="text-sm text-foreground/80 mt-1">{vote.bill_short_title}</p>
            )}
          </div>
          <Separator />
        </Fragment>
      )}

      {/* Vote ID */}
      <div>
        <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
          Vote ID
        </h3>
        <p className="text-sm font-mono text-foreground/80">{vote.vote_id}</p>
      </div>

      {/* External link */}
      {vote.bill_id && (
        <Fragment key="external-link">
          <Separator />
          <a
            href={`https://clerk.house.gov/Votes/${vote.vote_id.split("-").pop()}`}
            target="_blank"
            rel="noopener noreferrer"
            className="cursor-pointer inline-flex items-center gap-1.5 text-sm text-accent hover:text-accent/80"
          >
            View on {getChamberShortName(vote.chamber)} Clerk
            <svg
              className="w-3.5 h-3.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
              />
            </svg>
          </a>
        </Fragment>
      )}
    </div>
  );

  return (
    <ChatContextProvider
      context={{
        type: "vote",
        data: {
          vote_id: vote.vote_id,
          chamber: vote.chamber,
          question: vote.question,
          result: vote.result,
          date: vote.date,
          total_yea: vote.total_yea,
          total_nay: vote.total_nay,
        },
      }}
    >
    <main className="min-h-screen bg-background">
      <GridContainer className="py-8">
        {/* Header — matches legislation page */}
        <div className="mb-6">
          <Link
            href={routes.calendar.index}
            className="cursor-pointer inline-flex items-center gap-0.5 text-sm text-muted-foreground hover:text-foreground transition-colors mb-2"
          >
            <ChevronLeft className="size-4" />
            Back
          </Link>
          <h1 className="text-3xl font-bold text-foreground mb-1">
            {vote.question}
          </h1>
          {vote.bill_short_title && (
            <h2 className="text-lg text-foreground/80">
              {vote.bill_short_title}
            </h2>
          )}
        </div>

        <Separator className="mb-6" />

        {/* Tabs sit right below the separator */}
        <VoteDetailContent
          vote={vote}
          overlaySeats={overlaySeats}
          sidebar={sidebar}
        />
      </GridContainer>
    </main>
    </ChatContextProvider>
  );
}
