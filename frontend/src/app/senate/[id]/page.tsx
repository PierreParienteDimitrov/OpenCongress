import { notFound, redirect } from "next/navigation";

import { getMember } from "@/lib/api";
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

  return <MemberProfile member={member} />;
}
