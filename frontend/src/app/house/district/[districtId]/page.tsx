import { notFound } from "next/navigation";
import type { Metadata } from "next";

import { getRepresentatives } from "@/lib/api";
import { getStateName } from "@/lib/utils";
import DistrictDetailClient from "@/components/map/DistrictDetailClient";

interface PageProps {
  params: Promise<{ districtId: string }>;
}

const VALID_STATES = new Set([
  "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL",
  "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME",
  "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH",
  "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI",
  "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI",
  "WY", "PR", "GU", "VI", "AS", "MP",
]);

function parseDistrictId(districtId: string): { stateCode: string; districtNum: number } | null {
  const parts = districtId.split("-");
  if (parts.length !== 2) return null;

  const stateCode = parts[0].toUpperCase();
  const districtNum = parseInt(parts[1], 10);

  if (!VALID_STATES.has(stateCode)) return null;
  if (isNaN(districtNum) || districtNum < 0) return null;

  return { stateCode, districtNum };
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { districtId } = await params;
  const parsed = parseDistrictId(districtId);

  if (!parsed) {
    return { title: "District Not Found - OpenCongress" };
  }

  const { stateCode, districtNum } = parsed;
  const stateName = getStateName(stateCode);
  const label =
    districtNum === 0
      ? `${stateName} At-Large`
      : `${stateName} District ${districtNum}`;

  return {
    title: `${label} Representative - OpenCongress`,
    description: `View the U.S. Representative for ${label}.`,
  };
}

export const revalidate = 3600;

export default async function DistrictDetailPage({ params }: PageProps) {
  const { districtId } = await params;
  const parsed = parseDistrictId(districtId);

  if (!parsed) {
    notFound();
  }

  const { stateCode, districtNum } = parsed;

  // Fetch all representatives for this state (for district coloring on the map)
  const data = await getRepresentatives({ state: stateCode, page_size: "100" });
  const stateMembers = data.results;

  // Find the specific representative for this district
  const representative =
    stateMembers.find((m) => m.district === districtNum) ?? null;

  return (
    <DistrictDetailClient
      stateCode={stateCode}
      districtNum={districtNum}
      stateMembers={stateMembers}
      representative={representative}
    />
  );
}
