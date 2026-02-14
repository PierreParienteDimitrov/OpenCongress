import type { MetadataRoute } from "next";

import { getAllSenators, getAllRepresentatives } from "@/lib/api";
import { slugifyName } from "@/lib/utils";

const BASE_URL = "https://www.opencongress.app";

const STATE_CODES = [
  "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
  "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
  "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
  "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
  "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
  "DC",
];

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticPages: MetadataRoute.Sitemap = [
    { url: BASE_URL, changeFrequency: "daily", priority: 1.0 },
    { url: `${BASE_URL}/senate`, changeFrequency: "daily", priority: 0.9 },
    { url: `${BASE_URL}/house`, changeFrequency: "daily", priority: 0.9 },
    { url: `${BASE_URL}/calendar`, changeFrequency: "daily", priority: 0.7 },
    { url: `${BASE_URL}/this-week`, changeFrequency: "weekly", priority: 0.8 },
    { url: `${BASE_URL}/documentation`, changeFrequency: "monthly", priority: 0.3 },
  ];

  const [senators, representatives] = await Promise.all([
    getAllSenators(),
    getAllRepresentatives(),
  ]);

  const memberPages: MetadataRoute.Sitemap = [
    ...senators.map((m) => ({
      url: `${BASE_URL}/senate/${m.bioguide_id}-${slugifyName(m.full_name)}`,
      changeFrequency: "weekly" as const,
      priority: 0.8,
    })),
    ...representatives.map((m) => ({
      url: `${BASE_URL}/house/${m.bioguide_id}-${slugifyName(m.full_name)}`,
      changeFrequency: "weekly" as const,
      priority: 0.7,
    })),
  ];

  const statePages: MetadataRoute.Sitemap = STATE_CODES.map((s) => ({
    url: `${BASE_URL}/senate/state/${s}`,
    changeFrequency: "weekly" as const,
    priority: 0.6,
  }));

  return [...staticPages, ...memberPages, ...statePages];
}
