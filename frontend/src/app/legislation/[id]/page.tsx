import { notFound } from "next/navigation";
import Link from "next/link";

import { getBill } from "@/lib/api";
import { GridContainer } from "@/components/layout/GridContainer";
import { routes, getMemberRoute } from "@/lib/routes";
import {
  formatDate,
  getPartyBgColor,
  getResultBgColor,
  getResultLabel,
  getChamberShortName,
} from "@/lib/utils";
import type { VoteSummary } from "@/types";

export const revalidate = 86400; // 24 hours

interface PageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: PageProps) {
  const { id } = await params;
  try {
    const bill = await getBill(id);
    return {
      title: `${bill.display_number} - ${bill.short_title || bill.title}`,
      description: bill.summary_text || bill.title,
    };
  } catch {
    return {
      title: "Bill Not Found",
    };
  }
}

function VoteCard({ vote }: { vote: VoteSummary }) {
  const totalVotes = vote.total_yea + vote.total_nay;
  const yeaPercent = totalVotes > 0 ? (vote.total_yea / totalVotes) * 100 : 0;

  return (
    <div className="border rounded-lg p-4 bg-card shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm text-muted-foreground">
          {getChamberShortName(vote.chamber)} &middot; {formatDate(vote.date)}
        </span>
        <span className={`px-2 py-1 rounded text-sm font-medium ${getResultBgColor(vote.result)}`}>
          {getResultLabel(vote.result)}
        </span>
      </div>

      <p className="text-sm text-foreground/80 mb-3">{vote.question}</p>

      {/* Vote bar */}
      <div className="mb-3">
        <div className="flex h-4 rounded-full overflow-hidden bg-secondary">
          <div
            className="bg-green-500 transition-all"
            style={{ width: `${yeaPercent}%` }}
          />
          <div
            className="bg-red-500 transition-all"
            style={{ width: `${100 - yeaPercent}%` }}
          />
        </div>
        <div className="flex justify-between text-sm mt-1">
          <span className="text-green-600 font-medium">
            Yea: {vote.total_yea}
          </span>
          <span className="text-red-600 font-medium">
            Nay: {vote.total_nay}
          </span>
        </div>
      </div>

      {/* Party breakdown */}
      <div className="grid grid-cols-3 gap-2 text-xs">
        <div className="bg-blue-50 rounded p-2">
          <div className="font-medium text-blue-800">Democrats</div>
          <div className="text-blue-600">
            {vote.dem_yea} Y / {vote.dem_nay} N
          </div>
        </div>
        <div className="bg-red-50 rounded p-2">
          <div className="font-medium text-red-800">Republicans</div>
          <div className="text-red-600">
            {vote.rep_yea} Y / {vote.rep_nay} N
          </div>
        </div>
        <div className="bg-violet-50 rounded p-2">
          <div className="font-medium text-violet-800">Independents</div>
          <div className="text-violet-600">
            {vote.ind_yea} Y / {vote.ind_nay} N
          </div>
        </div>
      </div>

      {vote.is_bipartisan && (
        <div className="mt-2">
          <span className="inline-block px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded">
            Bipartisan
          </span>
        </div>
      )}
    </div>
  );
}

export default async function LegislationPage({ params }: PageProps) {
  const { id } = await params;

  let bill;
  try {
    bill = await getBill(id);
  } catch {
    notFound();
  }

  return (
    <main className="min-h-screen bg-background">
      <GridContainer className="py-8">
        {/* Header */}
        <div className="mb-6">
          <Link
            href={routes.calendar.index}
            className="text-accent hover:text-accent/80 text-sm mb-2 inline-block"
          >
            &larr; Back to Calendar
          </Link>
          <h1 className="text-3xl font-bold text-foreground mb-2">
            {bill.display_number}
          </h1>
          <h2 className="text-xl text-foreground/80">
            {bill.short_title || bill.title}
          </h2>
        </div>

        {/* Sponsor */}
        {bill.sponsor && (
          <div className="bg-card rounded-lg shadow-sm p-4 mb-6">
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Sponsor</h3>
            <div className="flex items-center gap-3">
              {bill.sponsor.photo_url && (
                <img
                  src={bill.sponsor.photo_url}
                  alt={bill.sponsor.full_name}
                  className="w-12 h-12 rounded-full object-cover"
                />
              )}
              <div>
                <Link
                  href={getMemberRoute(bill.sponsor.bioguide_id, bill.sponsor.chamber)}
                  className="text-accent hover:text-accent/80 font-medium"
                >
                  {bill.sponsor.full_name}
                </Link>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-medium ${getPartyBgColor(bill.sponsor.party)}`}
                  >
                    {bill.sponsor.party}
                  </span>
                  <span>
                    {bill.sponsor.state}
                    {bill.sponsor.district !== null &&
                      `-${bill.sponsor.district}`}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Bill Details */}
        <div className="bg-card rounded-lg shadow-sm p-6 mb-6">
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <span className="text-sm text-muted-foreground">Congress</span>
              <p className="font-medium">{bill.congress}th Congress</p>
            </div>
            <div>
              <span className="text-sm text-muted-foreground">Introduced</span>
              <p className="font-medium">{formatDate(bill.introduced_date)}</p>
            </div>
          </div>

          {/* Latest Action */}
          <div className="border-t pt-4">
            <h3 className="text-sm font-medium text-muted-foreground mb-2">
              Latest Action
            </h3>
            <p className="text-foreground/80">
              {bill.latest_action_text || "No action recorded"}
            </p>
            {bill.latest_action_date && (
              <p className="text-sm text-muted-foreground mt-1">
                {formatDate(bill.latest_action_date)}
              </p>
            )}
          </div>
        </div>

        {/* Summary */}
        {(bill.ai_summary || bill.summary_text) && (
          <div className="bg-card rounded-lg shadow-sm p-6 mb-6">
            <h3 className="text-lg font-semibold text-foreground mb-3">Summary</h3>
            {bill.ai_summary ? (
              <div>
                <p className="text-foreground/80 whitespace-pre-wrap">
                  {bill.ai_summary}
                </p>
                <p className="text-xs text-muted-foreground/60 mt-2">AI-generated summary</p>
              </div>
            ) : bill.summary_html ? (
              <div
                className="prose prose-sm max-w-none text-foreground/80"
                dangerouslySetInnerHTML={{ __html: bill.summary_html }}
              />
            ) : (
              <p className="text-foreground/80">{bill.summary_text}</p>
            )}
          </div>
        )}

        {/* Votes */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-foreground mb-3">
            Votes ({bill.votes.length})
          </h3>
          {bill.votes.length > 0 ? (
            <div className="space-y-4">
              {bill.votes.map((vote) => (
                <VoteCard key={vote.vote_id} vote={vote} />
              ))}
            </div>
          ) : (
            <div className="bg-card rounded-lg shadow-sm p-6 text-center text-muted-foreground">
              No votes recorded for this legislation yet.
            </div>
          )}
        </div>

        {/* External Link */}
        {bill.congress_url && (
          <div className="text-center">
            <a
              href={bill.congress_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-accent hover:text-accent/80"
            >
              View on Congress.gov
              <svg
                className="w-4 h-4"
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
          </div>
        )}
      </GridContainer>
    </main>
  );
}
