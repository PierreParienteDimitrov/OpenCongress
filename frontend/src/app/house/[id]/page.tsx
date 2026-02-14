import { notFound, redirect } from "next/navigation";

import { getMember } from "@/lib/api";
import { routes } from "@/lib/routes";
import { extractBioguideId, slugifyName } from "@/lib/utils";
import { ChatContextProvider } from "@/lib/chat-context";
import { JsonLd } from "@/components/seo/JsonLd";
import MemberProfile from "@/components/member/MemberProfile";

export const revalidate = 3600; // 1 hour

interface PageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: PageProps) {
  const { id } = await params;
  const bioguideId = extractBioguideId(id);
  try {
    const member = await getMember(bioguideId);
    const title = `Rep. ${member.full_name} (${member.party}-${member.state})`;
    const description = `Profile and voting record for Representative ${member.full_name}`;
    const canonicalSlug = `${member.bioguide_id}-${slugifyName(member.full_name)}`;
    return {
      title,
      description,
      alternates: {
        canonical: `/house/${canonicalSlug}`,
      },
      openGraph: {
        title,
        description,
        url: `/house/${canonicalSlug}`,
        type: "profile" as const,
        images: member.photo_url
          ? [{ url: member.photo_url, alt: member.full_name }]
          : undefined,
      },
      twitter: {
        card: "summary" as const,
        title,
        description,
        images: member.photo_url ? [member.photo_url] : undefined,
      },
    };
  } catch {
    return {
      title: "Representative Not Found",
    };
  }
}

export default async function RepresentativePage({ params }: PageProps) {
  const { id } = await params;
  const bioguideId = extractBioguideId(id);

  let member;
  try {
    member = await getMember(bioguideId);
  } catch {
    notFound();
  }

  // Redirect to correct route if this is a senator
  if (member.chamber === "senate") {
    redirect(routes.senate.detail(member.bioguide_id, member.full_name));
  }

  // Redirect to canonical URL with name slug if missing
  const expectedSlug = `${member.bioguide_id}-${slugifyName(member.full_name)}`;
  if (id !== expectedSlug) {
    redirect(`/house/${expectedSlug}`);
  }

  return (
    <ChatContextProvider
      context={{
        type: "member",
        data: {
          bioguide_id: member.bioguide_id,
          full_name: member.full_name,
          party: member.party,
          state: member.state,
          chamber: member.chamber,
        },
      }}
    >
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "Person",
          name: member.full_name,
          jobTitle: "United States Representative",
          worksFor: {
            "@type": "GovernmentOrganization",
            name: "United States House of Representatives",
          },
          image: member.photo_url || undefined,
          url: `https://www.opencongress.app/house/${expectedSlug}`,
          sameAs: [
            member.website_url,
            member.twitter_handle
              ? `https://x.com/${member.twitter_handle}`
              : null,
          ].filter(Boolean),
        }}
      />
      <MemberProfile member={member} />
    </ChatContextProvider>
  );
}
