import Image from "next/image";
import Link from "next/link";
import sanitizeHtml from "sanitize-html";
import { ChevronLeft, FileX2 } from "lucide-react";

import { getBill } from "@/lib/api";
import { GridContainer } from "@/components/layout/GridContainer";
import { ChatContextProvider } from "@/lib/chat-context";
import { routes, getMemberRoute } from "@/lib/routes";
import {
  cn,
  formatDate,
  getPartyBgColor,
  getResultBgColor,
  getResultLabel,
  getChamberShortName,
} from "@/lib/utils";
import type { VoteSummary } from "@/types";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { JsonLd } from "@/components/seo/JsonLd";

export const revalidate = 86400; // 24 hours

interface PageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: PageProps) {
  const { id } = await params;
  try {
    const bill = await getBill(id);
    const title = `${bill.display_number} - ${bill.short_title || bill.title}`;
    const description = bill.summary_text
      ? bill.summary_text.slice(0, 160)
      : bill.title;
    return {
      title,
      description,
      alternates: { canonical: `/legislation/${id}` },
      openGraph: {
        title,
        description,
        url: `/legislation/${id}`,
        type: "article",
      },
      twitter: {
        card: "summary",
        title,
        description,
      },
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
    <div className="py-4 first:pt-0">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-muted-foreground">
          {getChamberShortName(vote.chamber)} &middot; {formatDate(vote.date)}
        </span>
        <Badge className={cn(getResultBgColor(vote.result))}>
          {getResultLabel(vote.result)}
        </Badge>
      </div>

      <p className="text-sm text-foreground/80 mb-3">{vote.question}</p>

      {/* Vote bar */}
      <div className="mb-3">
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

      {/* Party breakdown */}
      <div className="grid grid-cols-3 gap-3 text-xs">
        <div>
          <div className="font-medium text-glory-blue-500 dark:text-glory-blue-300">Democrats</div>
          <div className="text-muted-foreground">
            {vote.dem_yea} Y / {vote.dem_nay} N
          </div>
        </div>
        <div>
          <div className="font-medium text-glory-red-500 dark:text-glory-red-400">Republicans</div>
          <div className="text-muted-foreground">
            {vote.rep_yea} Y / {vote.rep_nay} N
          </div>
        </div>
        <div>
          <div className="font-medium text-violet-600 dark:text-violet-400">Independents</div>
          <div className="text-muted-foreground">
            {vote.ind_yea} Y / {vote.ind_nay} N
          </div>
        </div>
      </div>

      {vote.is_bipartisan && (
        <div className="mt-2">
          <Badge className="bg-violet-600 text-white">
            Bipartisan
          </Badge>
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
    return (
      <main className="min-h-screen bg-background">
        <GridContainer className="py-8">
          <Link
            href={routes.home}
            className="cursor-pointer inline-flex items-center gap-0.5 text-sm text-muted-foreground hover:text-foreground transition-colors mb-6"
          >
            <ChevronLeft className="size-4" />
            Back
          </Link>
          <Alert className="max-w-lg">
            <FileX2 className="size-4" />
            <AlertTitle>Bill not found</AlertTitle>
            <AlertDescription>
              We don&apos;t have data for this bill yet. It may not have been
              indexed or the bill ID may be incorrect.
            </AlertDescription>
          </Alert>
        </GridContainer>
      </main>
    );
  }

  return (
    <ChatContextProvider
      context={{
        type: "bill",
        data: {
          bill_id: bill.bill_id,
          display_number: bill.display_number,
          title: bill.short_title || bill.title,
          sponsor_name: bill.sponsor?.full_name,
          latest_action: bill.latest_action_text,
          summary: bill.ai_summary || bill.summary_text || "",
        },
      }}
    >
    <JsonLd
      data={{
        "@context": "https://schema.org",
        "@type": "Article",
        headline: bill.short_title || bill.title,
        description: bill.summary_text || bill.title,
        url: `https://www.opencongress.app/legislation/${bill.bill_id}`,
        datePublished: bill.introduced_date || undefined,
      }}
    />
    <main className="min-h-screen bg-background">
      <GridContainer className="py-8">
        {/* Header */}
        <div className="mb-6">
          <Link
            href={routes.home}
            className="cursor-pointer inline-flex items-center gap-0.5 text-sm text-muted-foreground hover:text-foreground transition-colors mb-2"
          >
            <ChevronLeft className="size-4" />
            Back
          </Link>
          <h1 className="text-3xl font-bold text-foreground mb-1">
            {bill.display_number}
          </h1>
          <h2 className="text-lg text-foreground/80">
            {bill.short_title || bill.title}
          </h2>
        </div>

        <Separator className="mb-6" />

        {/* Three-column layout */}
        <div className="grid grid-cols-1 lg:grid-cols-[240px_1fr_280px] gap-6 lg:gap-8">
          {/* Left column — Bill data */}
          <div className="space-y-5">
            {/* Sponsor */}
            {bill.sponsor && (
              <div>
                <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
                  Sponsor
                </h3>
                <div className="flex items-center gap-3">
                  {bill.sponsor.photo_url && (
                    <Image
                      src={bill.sponsor.photo_url}
                      alt={bill.sponsor.full_name}
                      width={40}
                      height={40}
                      className="w-10 h-10 rounded-full object-cover"
                    />
                  )}
                  <div>
                    <Link
                      href={getMemberRoute(bill.sponsor.bioguide_id, bill.sponsor.chamber, bill.sponsor.full_name)}
                      className="cursor-pointer text-accent hover:text-accent/80 text-sm font-medium"
                    >
                      {bill.sponsor.full_name}
                    </Link>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <Badge className={cn(getPartyBgColor(bill.sponsor.party))}>
                        {bill.sponsor.party}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {bill.sponsor.state}
                        {bill.sponsor.district !== null &&
                          `-${bill.sponsor.district}`}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <Separator />

            {/* Congress */}
            <div>
              <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                Congress
              </h3>
              <p className="text-sm font-medium">{bill.congress}th Congress</p>
            </div>

            {/* Introduced */}
            <div>
              <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                Introduced
              </h3>
              <p className="text-sm font-medium">{formatDate(bill.introduced_date)}</p>
            </div>

            <Separator />

            {/* Latest Action */}
            <div>
              <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                Latest Action
              </h3>
              <p className="text-sm text-foreground/80">
                {bill.latest_action_text || "No action recorded"}
              </p>
              {bill.latest_action_date && (
                <p className="text-xs text-muted-foreground mt-1">
                  {formatDate(bill.latest_action_date)}
                </p>
              )}
            </div>

            {/* External Link */}
            {bill.congress_url && (
              <>
                <Separator />
                <a
                  href={bill.congress_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="cursor-pointer inline-flex items-center gap-1.5 text-sm text-accent hover:text-accent/80"
                >
                  View on Congress.gov
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
              </>
            )}
          </div>

          {/* Center column — Summary */}
          <div className="lg:border-l lg:border-r lg:border-border lg:px-8">
            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
              Summary
            </h3>
            {bill.ai_summary ? (
              <div>
                <div className="space-y-3 font-domine text-base text-foreground/80 leading-relaxed">
                  {bill.ai_summary.split("\n").map((para, i) => (
                    <p key={i}>{para}</p>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground/60 mt-3">AI-generated summary</p>
              </div>
            ) : bill.summary_html ? (
              <div
                className="max-w-none font-domine text-base text-foreground/80 leading-relaxed [&>p]:mb-3 [&>ul]:mb-3 [&>ul]:ml-5 [&>ul]:list-disc [&>ol]:mb-3 [&>ol]:ml-5 [&>ol]:list-decimal [&_li]:mb-1"
                dangerouslySetInnerHTML={{ __html: sanitizeHtml(bill.summary_html) }}
              />
            ) : bill.summary_text ? (
              <div className="space-y-3 font-domine text-base text-foreground/80 leading-relaxed">
                {bill.summary_text.split("\n").map((para, i) => (
                  <p key={i}>{para}</p>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No summary available.</p>
            )}
          </div>

          {/* Right column — Votes */}
          <div>
            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
              Votes ({bill.votes.length})
            </h3>
            {bill.votes.length > 0 ? (
              <div className="divide-y divide-border">
                {bill.votes.map((vote) => (
                  <VoteCard key={vote.vote_id} vote={vote} />
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                No votes recorded yet.
              </p>
            )}
          </div>
        </div>
      </GridContainer>
    </main>
    </ChatContextProvider>
  );
}
