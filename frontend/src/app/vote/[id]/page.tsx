import { notFound } from "next/navigation";
import Link from "next/link";

import { getVote, getSeatVoteOverlay } from "@/lib/api";
import { GridContainer } from "@/components/layout/GridContainer";
import { routes } from "@/lib/routes";
import {
  formatDate,
  getResultBgColor,
  getResultLabel,
  getChamberName,
} from "@/lib/utils";
import HemicycleChart from "@/components/hemicycle/HemicycleChart";

export const revalidate = 86400; // 24 hours

interface PageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: PageProps) {
  const { id } = await params;
  try {
    const vote = await getVote(id);
    return {
      title: `${vote.question} - ${getChamberName(vote.chamber)} Vote`,
      description: `${getResultLabel(vote.result)}: ${vote.total_yea} Yea, ${vote.total_nay} Nay`,
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

  const totalVotes = vote.total_yea + vote.total_nay;
  const yeaPercent = totalVotes > 0 ? (vote.total_yea / totalVotes) * 100 : 0;

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
          <div className="flex items-center gap-3 mb-2">
            <span className="text-sm text-muted-foreground">
              {getChamberName(vote.chamber)}
            </span>
            <span className="text-sm text-muted-foreground/60">•</span>
            <span className="text-sm text-muted-foreground">{formatDate(vote.date)}</span>
            {vote.time && (
              <>
                <span className="text-sm text-muted-foreground/60">•</span>
                <span className="text-sm text-muted-foreground">{vote.time}</span>
              </>
            )}
          </div>
          <h1 className="text-3xl font-bold text-foreground mb-3">
            {vote.question}
          </h1>
          <span
            className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getResultBgColor(vote.result)}`}
          >
            {getResultLabel(vote.result)}
          </span>
        </div>

        {/* Vote Results */}
        <div className="bg-card rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold text-foreground mb-4">Results</h2>

          {/* Vote bar */}
          <div className="mb-6">
            <div className="flex h-8 rounded-full overflow-hidden bg-secondary">
              <div
                className="bg-green-500 transition-all flex items-center justify-center text-white text-sm font-medium"
                style={{ width: `${yeaPercent}%` }}
              >
                {yeaPercent > 10 && `${vote.total_yea}`}
              </div>
              <div
                className="bg-red-500 transition-all flex items-center justify-center text-white text-sm font-medium"
                style={{ width: `${100 - yeaPercent}%` }}
              >
                {100 - yeaPercent > 10 && `${vote.total_nay}`}
              </div>
            </div>
            <div className="flex justify-between text-sm mt-2">
              <span className="text-green-600 font-medium">
                Yea: {vote.total_yea}
              </span>
              <span className="text-muted-foreground">
                Present: {vote.total_present} | Not Voting: {vote.total_not_voting}
              </span>
              <span className="text-red-600 font-medium">
                Nay: {vote.total_nay}
              </span>
            </div>
          </div>

          {/* Party breakdown */}
          <h3 className="text-md font-medium text-foreground/80 mb-3">Party Breakdown</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Democrats */}
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="font-medium text-blue-800 mb-2">Democrats</div>
              <div className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-green-600">Yea</span>
                  <span className="font-medium">{vote.dem_yea}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-red-600">Nay</span>
                  <span className="font-medium">{vote.dem_nay}</span>
                </div>
              </div>
              <div className="mt-2 h-2 rounded-full overflow-hidden bg-secondary">
                <div
                  className="h-full bg-green-500"
                  style={{
                    width: `${vote.dem_yea + vote.dem_nay > 0 ? (vote.dem_yea / (vote.dem_yea + vote.dem_nay)) * 100 : 0}%`,
                  }}
                />
              </div>
            </div>

            {/* Republicans */}
            <div className="bg-red-50 rounded-lg p-4">
              <div className="font-medium text-red-800 mb-2">Republicans</div>
              <div className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-green-600">Yea</span>
                  <span className="font-medium">{vote.rep_yea}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-red-600">Nay</span>
                  <span className="font-medium">{vote.rep_nay}</span>
                </div>
              </div>
              <div className="mt-2 h-2 rounded-full overflow-hidden bg-secondary">
                <div
                  className="h-full bg-green-500"
                  style={{
                    width: `${vote.rep_yea + vote.rep_nay > 0 ? (vote.rep_yea / (vote.rep_yea + vote.rep_nay)) * 100 : 0}%`,
                  }}
                />
              </div>
            </div>

            {/* Independents */}
            <div className="bg-violet-50 rounded-lg p-4">
              <div className="font-medium text-violet-800 mb-2">Independents</div>
              <div className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-green-600">Yea</span>
                  <span className="font-medium">{vote.ind_yea}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-red-600">Nay</span>
                  <span className="font-medium">{vote.ind_nay}</span>
                </div>
              </div>
              <div className="mt-2 h-2 rounded-full overflow-hidden bg-secondary">
                <div
                  className="h-full bg-green-500"
                  style={{
                    width: `${vote.ind_yea + vote.ind_nay > 0 ? (vote.ind_yea / (vote.ind_yea + vote.ind_nay)) * 100 : 0}%`,
                  }}
                />
              </div>
            </div>
          </div>

          {vote.is_bipartisan && (
            <div className="mt-4">
              <span className="inline-block px-3 py-1 bg-purple-100 text-purple-700 text-sm rounded-full">
                Bipartisan Vote
              </span>
            </div>
          )}
        </div>

        {/* Hemicycle Seat Map */}
        {overlaySeats.length > 0 && (
          <div className="bg-card rounded-lg shadow-sm p-6 mb-6">
            <h2 className="text-lg font-semibold text-foreground mb-3">
              Seat Map
            </h2>
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
                  Aura = party color
                </span>
              </div>
            </div>
            <div className="h-[400px]">
              <HemicycleChart
                chamber={vote.chamber}
                seats={overlaySeats}
                showVoteOverlay
              />
            </div>
          </div>
        )}

        {/* Vote ID */}
        <div className="bg-card rounded-lg shadow-sm p-6">
          <div className="text-sm text-muted-foreground">
            Vote ID: <span className="font-mono">{vote.vote_id}</span>
          </div>
        </div>
      </GridContainer>
    </main>
  );
}
