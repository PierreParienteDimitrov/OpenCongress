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
      title: `Rep. ${member.full_name} (${member.party}-${member.state})`,
      description: `Profile and voting record for Representative ${member.full_name}`,
    };
  } catch {
    return {
      title: "Representative Not Found",
    };
  }
}

export default async function RepresentativePage({ params }: PageProps) {
  const { id } = await params;

  let member;
  try {
    member = await getMember(id);
  } catch {
    notFound();
  }

  // Redirect to correct route if this is a senator
  if (member.chamber === "senate") {
    redirect(`/senate/${id}`);
  }

  return (
    <ChatContextProvider
      context={{
        type: "member",
        data: {
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
