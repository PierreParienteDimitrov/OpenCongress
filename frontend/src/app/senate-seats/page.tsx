import Link from "next/link";
import type { Metadata } from "next";

import { getSeats, getVotes } from "@/lib/api";
import { routes } from "@/lib/routes";
import HemicyclePageClient from "@/components/hemicycle/HemicyclePageClient";

export const metadata: Metadata = {
  title: "Senate Seat Map - OpenCongress",
  description:
    "Interactive hemicycle visualization of the U.S. Senate showing all 100 seats by party and vote.",
};

export const revalidate = 86400;

export default async function SenateSeatsPage() {
  const [seats, votesResponse] = await Promise.all([
    getSeats("senate"),
    getVotes({ chamber: "senate", ordering: "-date" }),
  ]);

  return (
    <main className="flex h-screen flex-col bg-zinc-50 dark:bg-zinc-950">
      {/* Header — compact, constrained width */}
      <div className="mx-auto w-full max-w-4xl shrink-0 px-4 pt-4 pb-2 sm:px-6 lg:px-8">
        <Link
          href={routes.home}
          className="inline-flex items-center text-sm text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200"
        >
          &larr; Back to Home
        </Link>
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-50 sm:text-3xl">
          U.S. Senate Seat Map
        </h1>
      </div>

      {/* Hemicycle — fills remaining viewport */}
      <div className="min-h-0 flex-1 px-4 pb-4">
        <div className="flex h-full flex-col rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
          <HemicyclePageClient
            chamber="senate"
            initialSeats={seats}
            votes={votesResponse.results}
          />
        </div>
      </div>
    </main>
  );
}
