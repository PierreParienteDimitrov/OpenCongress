import { Suspense } from "react";
import type { Metadata } from "next";

import {
  getSenators,
  getAllSenators,
  getSeats,
  getVotes,
} from "@/lib/api";
import ChamberPageClient from "@/components/chamber/ChamberPageClient";

export const metadata: Metadata = {
  title: "U.S. Senate - OpenCongress",
  description:
    "Explore the U.S. Senate — seats, state map, and member directory.",
};

export const dynamic = "force-dynamic";
export const revalidate = 3600;

export default async function SenatePage() {
  const [initialData, allSenators, seats, votesResponse] = await Promise.all([
    getSenators({ ordering: "last_name" }),
    getAllSenators(),
    getSeats("senate"),
    getVotes({ chamber: "senate", ordering: "-date" }),
  ]);

  return (
    <Suspense>
      <ChamberPageClient
        chamber="senate"
        initialData={initialData}
        allMembers={allSenators}
        initialSeats={seats}
        votes={votesResponse.results}
        memberCount={initialData.count}
      />
    </Suspense>
  );
}
