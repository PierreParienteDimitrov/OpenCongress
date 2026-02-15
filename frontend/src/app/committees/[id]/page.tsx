import { notFound, redirect } from "next/navigation";
import type { Metadata } from "next";

import CommitteeProfile from "@/components/committee/CommitteeProfile";
import { getCommittee } from "@/lib/api";
import { ChatContextProvider } from "@/lib/chat-context";
import { extractCommitteeId, slugifyName } from "@/lib/utils";

export const revalidate = 3600;

interface PageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { id } = await params;
  const committeeId = extractCommitteeId(id);

  try {
    const committee = await getCommittee(committeeId);
    const title = `${committee.name} — OpenCongress`;
    const description = committee.ai_summary
      ? committee.ai_summary.substring(0, 160)
      : `Explore the ${committee.name} — members, leadership, subcommittees, and referred legislation.`;
    const canonicalSlug = `${committee.committee_id}-${slugifyName(committee.name)}`;

    return {
      title,
      description,
      alternates: { canonical: `/committees/${canonicalSlug}` },
      openGraph: {
        title,
        description,
        url: `/committees/${canonicalSlug}`,
        type: "website",
      },
      twitter: {
        card: "summary",
        title,
        description,
      },
    };
  } catch {
    return { title: "Committee Not Found — OpenCongress" };
  }
}

export default async function CommitteeDetailPage({ params }: PageProps) {
  const { id } = await params;
  const committeeId = extractCommitteeId(id);

  let committee;
  try {
    committee = await getCommittee(committeeId);
  } catch {
    notFound();
  }

  // Redirect to canonical URL with name slug if missing
  const expectedSlug = `${committee.committee_id}-${slugifyName(committee.name)}`;
  if (id !== expectedSlug) {
    redirect(`/committees/${expectedSlug}`);
  }

  return (
    <ChatContextProvider
      context={{
        type: "committee",
        data: {
          committee_id: committee.committee_id,
          name: committee.name,
          chamber: committee.chamber,
        },
      }}
    >
      <CommitteeProfile committee={committee} />
    </ChatContextProvider>
  );
}
