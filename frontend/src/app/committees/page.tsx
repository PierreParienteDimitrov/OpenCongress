import { Suspense } from "react";
import type { Metadata } from "next";

import CommitteeList from "@/components/committee/CommitteeList";
import { GridContainer } from "@/components/layout/GridContainer";
import { getCommittees } from "@/lib/api";

export const metadata: Metadata = {
  title: "Committees — OpenCongress",
  description:
    "Explore all congressional committees — membership, leadership, referred legislation, and AI-generated summaries.",
  alternates: { canonical: "/committees" },
  openGraph: {
    title: "Committees — OpenCongress",
    description:
      "Explore all congressional committees — membership, leadership, referred legislation, and AI-generated summaries.",
    url: "/committees",
    type: "website",
  },
  twitter: {
    card: "summary",
    title: "Committees — OpenCongress",
    description:
      "Explore all congressional committees — membership, leadership, referred legislation, and AI-generated summaries.",
  },
};

export const dynamic = "force-dynamic";
export const revalidate = 3600;

export default async function CommitteesPage() {
  const initialData = await getCommittees({
    ordering: "name",
  });

  return (
    <main className="min-h-screen bg-background">
      <GridContainer className="py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-foreground">Committees</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Congressional committees and their members, leadership, and referred
            legislation.
          </p>
        </div>

        <Suspense>
          <CommitteeList initialData={initialData} />
        </Suspense>
      </GridContainer>
    </main>
  );
}
