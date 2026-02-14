import { notFound } from "next/navigation";
import type { Metadata } from "next";

import { getSenators } from "@/lib/api";
import { getStateName } from "@/lib/utils";
import StateDetailClient from "@/components/map/StateDetailClient";

interface PageProps {
  params: Promise<{ stateCode: string }>;
}

// All valid US state codes
const VALID_STATES = new Set([
  "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL",
  "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME",
  "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH",
  "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI",
  "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI",
  "WY", "PR", "GU", "VI", "AS", "MP",
]);

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { stateCode } = await params;
  const upper = stateCode.toUpperCase();
  const stateName = getStateName(upper);

  const title = `${stateName} Senators - OpenCongress`;
  const description = `View the U.S. Senators representing ${stateName}.`;
  return {
    title,
    description,
    alternates: { canonical: `/senate/state/${upper}` },
    openGraph: { title, description, url: `/senate/state/${upper}` },
    twitter: { card: "summary" as const, title, description },
  };
}

export const revalidate = 3600;

export default async function StateDetailPage({ params }: PageProps) {
  const { stateCode } = await params;
  const upper = stateCode.toUpperCase();

  if (!VALID_STATES.has(upper)) {
    notFound();
  }

  const data = await getSenators({ state: upper, page_size: "10" });

  return <StateDetailClient stateCode={upper} senators={data.results} />;
}
