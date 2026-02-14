import { notFound } from "next/navigation";
import Link from "next/link";

import { getVote, getSeatVoteOverlay } from "@/lib/api";
import { GridContainer } from "@/components/layout/GridContainer";
import { ChatContextProvider } from "@/lib/chat-context";
import { routes } from "@/lib/routes";
import {
  cn,
  formatDate,
  getResultBgColor,
  getResultLabel,
  getChamberName,
} from "@/lib/utils";
import HemicycleWithZoom from "@/components/hemicycle/HemicycleWithZoom";
import VoteMemberTable from "@/components/vote/VoteMemberTable";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";

export const revalidate = 86400; // 24 hours

interface PageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: PageProps) {
  const { id } = await params;
  try {
    const vote = await getVote(id);
    const title = `${vote.question} - ${getChamberName(vote.chamber)} Vote`;
    const description = `${getResultLabel(vote.result)}: ${vote.total_yea} Yea, ${vote.total_nay} Nay`;
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

  const overlaySeats = await getSeatVoteOverlay(vote.chamber, vote.vote_id);


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
        {/* Header */}
        <div className="mb-6 pb-6">
          <Link
            href={routes.calendar.index}
            className="text-accent hover:text-accent/80 text-sm mb-2 inline-block"
          >
            &larr; Back to Calendar
          </Link>
          <div className="flex items-center gap-3 mb-2">
            <span className="text-sm text-muted-foreground">
              {getChamberName(vote.chamber)}
            </span>
            <span className="text-sm text-muted-foreground/60">&middot;</span>
            <span className="text-sm text-muted-foreground">{formatDate(vote.date)}</span>
            {vote.time && (
              <>
                <span className="text-sm text-muted-foreground/60">&middot;</span>
                <span className="text-sm text-muted-foreground">{vote.time}</span>
              </>
            )}
          </div>
          <h1 className="text-3xl font-bold text-foreground mb-3">
            {vote.question}
          </h1>
          <div className="flex flex-wrap items-center gap-2">
            <Badge className={cn("text-sm px-3 py-1", getResultBgColor(vote.result))}>
              {getResultLabel(vote.result)}
            </Badge>
            {vote.is_bipartisan && (
              <Badge className="bg-purple-100 text-purple-700 text-sm">
                Bipartisan Vote
              </Badge>
            )}
          </div>
        </div>

        <Separator className="mb-6" />

        {/* Vote Results */}
        <div className="mb-6 pb-6">
          <h2 className="text-lg font-semibold mb-4">Results</h2>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div className="flex flex-col items-center gap-1 rounded-sm bg-white/90 dark:bg-white/10 p-4">
              <span className="text-3xl font-bold text-foreground">{vote.total_yea}</span>
              <span className="text-sm font-medium text-muted-foreground">Yea</span>
            </div>
            <div className="flex flex-col items-center gap-1 rounded-sm p-4" style={{ backgroundColor: "#18181b" }}>
              <span className="text-3xl font-bold text-white">{vote.total_nay}</span>
              <span className="text-sm font-medium text-white/60">Nay</span>
            </div>
            <div className="flex flex-col items-center gap-1 rounded-sm bg-yellow-500/20 p-4">
              <span className="text-3xl font-bold text-foreground">{vote.total_present}</span>
              <span className="text-sm font-medium text-muted-foreground">Present</span>
            </div>
            <div className="flex flex-col items-center gap-1 rounded-sm bg-secondary p-4">
              <span className="text-3xl font-bold text-foreground">{vote.total_not_voting}</span>
              <span className="text-sm font-medium text-muted-foreground">Not Voting</span>
            </div>
          </div>

          {/* Party breakdown */}
          <div className="mt-6 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-muted-foreground">
                  <th className="text-left py-2 font-medium">Party</th>
                  <th className="text-right py-2 font-medium">Yea</th>
                  <th className="text-right py-2 font-medium">Nay</th>
                  <th className="text-right py-2 font-medium">Total</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-border/50">
                  <td className="py-2 text-glory-blue-500 font-medium">Democrats</td>
                  <td className="py-2 text-right">{vote.dem_yea}</td>
                  <td className="py-2 text-right">{vote.dem_nay}</td>
                  <td className="py-2 text-right font-medium">{vote.dem_yea + vote.dem_nay}</td>
                </tr>
                <tr className="border-b border-border/50">
                  <td className="py-2 text-glory-red-500 font-medium">Republicans</td>
                  <td className="py-2 text-right">{vote.rep_yea}</td>
                  <td className="py-2 text-right">{vote.rep_nay}</td>
                  <td className="py-2 text-right font-medium">{vote.rep_yea + vote.rep_nay}</td>
                </tr>
                <tr>
                  <td className="py-2 text-violet-500 font-medium">Independents</td>
                  <td className="py-2 text-right">{vote.ind_yea}</td>
                  <td className="py-2 text-right">{vote.ind_nay}</td>
                  <td className="py-2 text-right font-medium">{vote.ind_yea + vote.ind_nay}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Hemicycle Seat Map */}
        {overlaySeats.length > 0 && (
          <>
            <Separator className="mb-6" />
            <div className="mb-6 pb-6">
              <h2 className="text-lg font-semibold mb-4">Seat Map</h2>
              <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground mb-4">
                <div className="flex items-center gap-1.5">
                  <span className="inline-block h-3 w-3 rounded-full border border-border bg-white" />
                  <span>Yea</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: "#18181b" }} />
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
            </div>
          </>
        )}

        {/* Member Votes Table */}
        {overlaySeats.length > 0 && (
          <>
            <Separator className="mb-6" />
            <div className="mb-6 pb-6">
              <h2 className="text-lg font-semibold mb-4">Member Votes</h2>
              <VoteMemberTable seats={overlaySeats} chamber={vote.chamber} />
            </div>
          </>
        )}

        {/* Vote ID */}
        <Separator className="mb-6" />
        <div className="text-sm text-muted-foreground">
          Vote ID: <span className="font-mono">{vote.vote_id}</span>
        </div>
      </GridContainer>
    </main>
    </ChatContextProvider>
  );
}
