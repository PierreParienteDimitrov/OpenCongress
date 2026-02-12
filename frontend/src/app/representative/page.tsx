import Link from "next/link";
import type { Metadata } from "next";

import { getRepresentatives } from "@/lib/api";
import { GridContainer } from "@/components/layout/GridContainer";
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
    <main className="min-h-screen bg-background">
      <GridContainer className="py-8">
        {/* Header */}
        <div className="mb-8">
          <Link
            href={routes.home}
            className="mb-4 inline-flex items-center text-sm text-muted-foreground hover:text-foreground"
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
          <h1 className="text-3xl font-bold text-foreground sm:text-4xl">
            U.S. Representatives
          </h1>
          <p className="mt-2 text-lg text-muted-foreground">
            Browse all {initialData.count} current members of the U.S. House of Representatives.
          </p>
        </div>

        {/* Member List */}
        <RepresentativeList initialData={initialData} />
      </GridContainer>
    </main>
  );
}
