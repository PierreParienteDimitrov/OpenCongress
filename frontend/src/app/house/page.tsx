import { Suspense } from "react";
import type { Metadata } from "next";

import {
  getRepresentatives,
  getAllRepresentatives,
  getSeats,
  getVotes,
} from "@/lib/api";
import ChamberPageClient from "@/components/chamber/ChamberPageClient";

export const metadata: Metadata = {
  title: "U.S. House of Representatives - OpenCongress",
  description:
    "Explore the U.S. House of Representatives — seats, district map, and member directory.",
};

export const dynamic = "force-dynamic";
export const revalidate = 3600;

export default async function HousePage() {
  const [initialData, allRepresentatives, seats, votesResponse] =
    await Promise.all([
      getRepresentatives({ ordering: "last_name" }),
      getAllRepresentatives(),
      getSeats("house"),
      getVotes({ chamber: "house", ordering: "-date" }),
    ]);

  return (
    <Suspense>
      <ChamberPageClient
        chamber="house"
        initialData={initialData}
        allMembers={allRepresentatives}
        initialSeats={seats}
        votes={votesResponse.results}
        memberCount={initialData.count}
      />
    </Suspense>
  );
}
