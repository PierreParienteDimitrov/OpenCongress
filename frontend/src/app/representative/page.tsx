import Link from "next/link";
import type { Metadata } from "next";

import { getRepresentatives } from "@/lib/api";
import { routes } from "@/lib/routes";
import RepresentativeList from "./RepresentativeList";

export const metadata: Metadata = {
  title: "U.S. Representatives - OpenCongress",
  description: "Browse all current members of the U.S. House of Representatives, their party affiliations, and district representation.",
};

export const dynamic = "force-dynamic";
export const revalidate = 3600; // 1 hour

export default async function RepresentativesPage() {
  const initialData = await getRepresentatives({ ordering: "last_name" });

  return (
    <main className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <Link
            href={routes.home}
            className="mb-4 inline-flex items-center text-sm text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200"
          >
            <svg
              className="mr-1 h-4 w-4"
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
            Back to Home
          </Link>
          <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50 sm:text-4xl">
            U.S. Representatives
          </h1>
          <p className="mt-2 text-lg text-zinc-600 dark:text-zinc-400">
            Browse all {initialData.count} current members of the U.S. House of Representatives.
          </p>
        </div>

        {/* Member List */}
        <RepresentativeList initialData={initialData} />
      </div>
    </main>
  );
}
