import Link from "next/link";
import type { Metadata } from "next";

import { getSeats, getVotes } from "@/lib/api";
import { routes } from "@/lib/routes";
import HemicyclePageClient from "@/components/hemicycle/HemicyclePageClient";

export const metadata: Metadata = {
  title: "House Seat Map - OpenCongress",
  description:
    "Interactive hemicycle visualization of the U.S. House of Representatives showing all 435 seats by party and vote.",
};

export const revalidate = 86400;

export default async function HouseSeatsPage() {
  const [seats, votesResponse] = await Promise.all([
    getSeats("house"),
    getVotes({ chamber: "house", ordering: "-date" }),
  ]);

  return (
    <main className="flex h-[calc(100vh-var(--navbar-height))] flex-col bg-background">
      {/* Header — compact, constrained width */}
      <div className="mx-auto w-full max-w-4xl shrink-0 px-4 pt-4 pb-2 sm:px-6 lg:px-8">
        <Link
          href={routes.home}
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground"
        >
          &larr; Back to Home
        </Link>
        <h1 className="text-2xl font-bold text-foreground sm:text-3xl">
          U.S. House Seat Map
        </h1>
      </div>

      {/* Hemicycle — fills remaining viewport */}
      <div className="min-h-0 flex-1 px-4 pb-4">
        <div className="flex h-full flex-col rounded-xl border border-border bg-card p-4 shadow-sm ">
          <HemicyclePageClient
            chamber="house"
            initialSeats={seats}
            votes={votesResponse.results}
          />
        </div>
      </div>
    </main>
  );
}
