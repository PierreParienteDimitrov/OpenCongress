import { Suspense } from "react";
import type { Metadata } from "next";

import {
  getRepresentatives,
  getAllRepresentatives,
  getSeats,
  getVotes,
} from "@/lib/api";
import { ChatContextProvider } from "@/lib/chat-context";
import ChamberPageClient from "@/components/chamber/ChamberPageClient";

export const metadata: Metadata = {
  title: "U.S. House of Representatives - OpenCongress",
  description:
    "Explore the U.S. House of Representatives — seats, district map, and member directory.",
  alternates: { canonical: "/house" },
  openGraph: {
    title: "U.S. House of Representatives - OpenCongress",
    description:
      "Explore the U.S. House of Representatives — seats, district map, and member directory.",
    url: "/house",
  },
  twitter: {
    card: "summary",
    title: "U.S. House of Representatives - OpenCongress",
    description:
      "Explore the U.S. House of Representatives — seats, district map, and member directory.",
  },
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
    <ChatContextProvider context={{ type: "chamber", data: { chamber: "house" } }}>
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
    </ChatContextProvider>
  );
}
