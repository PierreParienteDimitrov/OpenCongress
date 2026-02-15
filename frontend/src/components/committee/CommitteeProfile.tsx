import Image from "next/image";
import Link from "next/link";
import {
  ExternalLink,
  FileText,
  FolderTree,
  Users,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { GridContainer } from "@/components/layout/GridContainer";
import { routes, getMemberRoute } from "@/lib/routes";
import { cn, getPartyBgColor } from "@/lib/utils";
import type { CommitteeDetail } from "@/types";

interface CommitteeProfileProps {
  committee: CommitteeDetail;
}

function getRoleBadgeColor(role: string): string {
  if (role === "chair") return "bg-amber-500 text-white";
  if (role === "ranking") return "bg-violet-500 text-white";
  return "bg-secondary text-secondary-foreground";
}

export default function CommitteeProfile({ committee }: CommitteeProfileProps) {
  // Sort members: chair first, then ranking, then regular members
  const sortedMembers = [...committee.members].sort((a, b) => {
    const order: Record<string, number> = { chair: 0, ranking: 1, member: 2 };
    return (order[a.role] ?? 3) - (order[b.role] ?? 3);
  });

  return (
    <main className="min-h-screen bg-background">
      <GridContainer className="py-8">
        {/* Header */}
        <div className="mb-6">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground">
                {committee.name}
              </h1>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <Badge
                  className={cn(
                    "text-sm",
                    committee.chamber === "senate"
                      ? "bg-glory-blue-500 text-white"
                      : "bg-glory-red-500 text-white"
                  )}
                >
                  {committee.chamber === "senate" ? "Senate" : "House"}
                </Badge>
                {committee.committee_type !== "standing" && (
                  <Badge variant="outline" className="text-sm capitalize">
                    {committee.committee_type}
                  </Badge>
                )}
              </div>
            </div>
            {committee.url && (
              <a
                href={committee.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex cursor-pointer items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
              >
                <ExternalLink className="size-4" />
                Congress.gov
              </a>
            )}
          </div>
        </div>

        <Separator className="mb-6" />

        {/* Three-column layout */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[240px_1fr_280px] lg:gap-8">
          {/* Left column — Quick facts */}
          <div className="space-y-5">
            <div>
              <h3 className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Quick Facts
              </h3>
              <dl className="mt-3 space-y-3 text-sm">
                <div>
                  <dt className="text-muted-foreground">Members</dt>
                  <dd className="font-medium text-foreground">
                    {committee.members.length}
                  </dd>
                </div>
                {committee.chair && (
                  <div>
                    <dt className="text-muted-foreground">Chair</dt>
                    <dd>
                      <Link
                        href={getMemberRoute(
                          committee.chair.bioguide_id,
                          committee.chamber,
                          committee.chair.full_name
                        )}
                        className="cursor-pointer font-medium text-foreground hover:underline"
                      >
                        {committee.chair.full_name}
                      </Link>
                      <span className="ml-1 text-xs text-muted-foreground">
                        ({committee.chair.party})
                      </span>
                    </dd>
                  </div>
                )}
                {committee.ranking_member && (
                  <div>
                    <dt className="text-muted-foreground">Ranking Member</dt>
                    <dd>
                      <Link
                        href={getMemberRoute(
                          committee.ranking_member.bioguide_id,
                          committee.chamber,
                          committee.ranking_member.full_name
                        )}
                        className="cursor-pointer font-medium text-foreground hover:underline"
                      >
                        {committee.ranking_member.full_name}
                      </Link>
                      <span className="ml-1 text-xs text-muted-foreground">
                        ({committee.ranking_member.party})
                      </span>
                    </dd>
                  </div>
                )}
                <div>
                  <dt className="text-muted-foreground">Subcommittees</dt>
                  <dd className="font-medium text-foreground">
                    {committee.subcommittees.length}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Referred Bills</dt>
                  <dd className="font-medium text-foreground">
                    {committee.referred_bills.length}
                  </dd>
                </div>
              </dl>
            </div>
          </div>

          {/* Center column — AI summary + subcommittees */}
          <div className="lg:border-l lg:border-r lg:border-border lg:px-8">
            <h3 className="mb-3 text-xs font-medium uppercase tracking-wide text-muted-foreground">
              About
            </h3>
            {committee.ai_summary ? (
              <div>
                <div className="space-y-3 font-domine text-base leading-relaxed text-foreground/80">
                  {committee.ai_summary.split("\n").map((para, i) => (
                    <p key={i}>{para}</p>
                  ))}
                </div>
                <p className="mt-3 text-xs text-muted-foreground/60">
                  AI-generated summary
                </p>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                No summary available yet.
              </p>
            )}

            {/* Subcommittees */}
            {committee.subcommittees.length > 0 && (
              <div className="mt-8">
                <h3 className="mb-3 flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  <FolderTree className="size-3.5" />
                  Subcommittees ({committee.subcommittees.length})
                </h3>
                <div className="space-y-2">
                  {committee.subcommittees.map((sub) => (
                    <Link
                      key={sub.committee_id}
                      href={routes.committees.detail(
                        sub.committee_id,
                        sub.name
                      )}
                      className="cursor-pointer"
                    >
                      <Card className="py-2 transition-colors hover:bg-accent/50">
                        <CardContent className="flex items-center justify-between py-0">
                          <span className="text-sm text-foreground">
                            {sub.name}
                          </span>
                          <span className="flex items-center gap-1 text-xs text-muted-foreground">
                            <Users className="size-3" />
                            {sub.member_count}
                          </span>
                        </CardContent>
                      </Card>
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right column — Members */}
          <div>
            <h3 className="mb-3 flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
              <Users className="size-3.5" />
              Members ({sortedMembers.length})
            </h3>
            <div className="space-y-2">
              {sortedMembers.map((member) => (
                <Link
                  key={member.bioguide_id}
                  href={getMemberRoute(
                    member.bioguide_id,
                    committee.chamber,
                    member.full_name
                  )}
                  className="flex cursor-pointer items-center gap-3 rounded-md px-2 py-1.5 transition-colors hover:bg-accent/50"
                >
                  {member.photo_url ? (
                    <Image
                      src={member.photo_url}
                      alt={member.full_name}
                      width={32}
                      height={32}
                      className="size-8 rounded-full object-cover"
                    />
                  ) : (
                    <div className="flex size-8 items-center justify-center rounded-full bg-secondary text-xs font-medium">
                      {member.full_name.charAt(0)}
                    </div>
                  )}
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-foreground">
                      {member.full_name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {member.state}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-1.5">
                    <Badge
                      className={cn(
                        "text-[10px] px-1.5 py-0",
                        getPartyBgColor(member.party)
                      )}
                    >
                      {member.party}
                    </Badge>
                    {member.role !== "member" && (
                      <Badge
                        className={cn(
                          "text-[10px] px-1.5 py-0",
                          getRoleBadgeColor(member.role)
                        )}
                      >
                        {member.role_display}
                      </Badge>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>

        {/* Referred legislation section */}
        {committee.referred_bills.length > 0 && (
          <div className="mt-10">
            <Separator className="mb-6" />
            <h3 className="mb-4 flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
              <FileText className="size-3.5" />
              Referred Legislation ({committee.referred_bills.length})
            </h3>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[120px]">Bill</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead className="w-[120px]">Sponsor</TableHead>
                  <TableHead className="w-[120px]">Latest Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {committee.referred_bills.map((bill) => (
                  <TableRow key={bill.bill_id}>
                    <TableCell>
                      <Link
                        href={routes.legislation.detail(bill.bill_id)}
                        className="cursor-pointer font-medium text-foreground hover:underline"
                      >
                        {bill.display_number}
                      </Link>
                    </TableCell>
                    <TableCell className="max-w-[300px] truncate text-sm text-muted-foreground">
                      {bill.short_title || bill.title}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {bill.sponsor_name || "—"}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {bill.latest_action_date || "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </GridContainer>
    </main>
  );
}
