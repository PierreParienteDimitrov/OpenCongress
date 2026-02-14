import { notFound, redirect } from "next/navigation";

import { getMember } from "@/lib/api";
import { ChatContextProvider } from "@/lib/chat-context";
import MemberProfile from "@/components/member/MemberProfile";

export const revalidate = 3600; // 1 hour

interface PageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: PageProps) {
  const { id } = await params;
  try {
    const member = await getMember(id);
    return {
      title: `Sen. ${member.full_name} (${member.party}-${member.state})`,
      description: `Profile and voting record for Senator ${member.full_name}`,
    };
  } catch {
    return {
      title: "Senator Not Found",
    };
  }
}

export default async function SenatorPage({ params }: PageProps) {
  const { id } = await params;

  let member;
  try {
    member = await getMember(id);
  } catch {
    notFound();
  }

  // Redirect to correct route if this is a representative
  if (member.chamber === "house") {
    redirect(`/house/${id}`);
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
      <MemberProfile member={member} />
    </ChatContextProvider>
  );
}
