import Link from "next/link";

import { GridContainer } from "@/components/layout/GridContainer";
import type { MemberDetail, MemberRecentVote } from "@/types";
import {
  cn,
  formatDate,
  getPartyBgColor,
  getPartyName,
  getMemberLocation,
  getPositionBgColor,
  getPositionLabel,
  getResultBgColor,
  getResultLabel,
  getChamberShortName,
} from "@/lib/utils";
import { routes } from "@/lib/routes";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface MemberProfileProps {
  member: MemberDetail;
}

function RecentVoteItem({ vote }: { vote: MemberRecentVote }) {
  return (
    <div className="border-b last:border-b-0 py-3">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <p className="text-sm text-foreground/80 truncate">{vote.description}</p>
          <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
            <span>{formatDate(vote.date)}</span>
            {vote.bill_display_number && vote.bill_id && (
              <Link
                href={routes.legislation.detail(vote.bill_id)}
                className="text-accent hover:text-accent/80"
              >
                {vote.bill_display_number}
              </Link>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Badge className={cn(getPositionBgColor(vote.position))}>
            {getPositionLabel(vote.position)}
          </Badge>
          <Badge className={cn(getResultBgColor(vote.result))}>
            {getResultLabel(vote.result)}
          </Badge>
        </div>
      </div>
    </div>
  );
}

export default function MemberProfile({ member }: MemberProfileProps) {
  const socialLinks = [
    member.twitter_handle && {
      label: "Twitter",
      url: `https://twitter.com/${member.twitter_handle}`,
      icon: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
        </svg>
      ),
    },
    member.facebook_id && {
      label: "Facebook",
      url: `https://facebook.com/${member.facebook_id}`,
      icon: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
        </svg>
      ),
    },
    member.youtube_id && {
      label: "YouTube",
      url: `https://youtube.com/${member.youtube_id}`,
      icon: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
        </svg>
      ),
    },
  ].filter(Boolean) as Array<{ label: string; url: string; icon: React.ReactNode }>;

  return (
    <main className="min-h-screen bg-background">
      <GridContainer className="py-8">
        {/* Header */}
        <Card className="mb-6 p-6 py-6">
          <div className="flex flex-col md:flex-row gap-6">
            {/* Photo */}
            <div className="shrink-0">
              {member.photo_url ? (
                <img
                  src={member.photo_url}
                  alt={member.full_name}
                  className="w-32 h-32 md:w-40 md:h-40 rounded-lg object-cover"
                />
              ) : (
                <div className="w-32 h-32 md:w-40 md:h-40 rounded-lg bg-secondary flex items-center justify-center">
                  <span className="text-4xl text-muted-foreground/60">
                    {member.first_name[0]}
                    {member.last_name[0]}
                  </span>
                </div>
              )}
            </div>

            {/* Info */}
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-foreground mb-2">
                {member.full_name}
              </h1>

              <div className="flex flex-wrap items-center gap-2 mb-4">
                <Badge className={cn("text-sm px-3 py-1", getPartyBgColor(member.party))}>
                  {getPartyName(member.party)}
                </Badge>
                <span className="text-muted-foreground">
                  {getChamberShortName(member.chamber)}
                </span>
                <span className="text-muted-foreground/60">&middot;</span>
                <span className="text-muted-foreground">
                  {getMemberLocation(member.state, member.district, member.chamber)}
                </span>
              </div>

              {/* Term info */}
              {(member.term_start || member.term_end) && (
                <p className="text-sm text-muted-foreground mb-4">
                  Term:{" "}
                  {member.term_start && formatDate(member.term_start)}
                  {member.term_start && member.term_end && " - "}
                  {member.term_end && formatDate(member.term_end)}
                </p>
              )}

              {/* Social links */}
              {socialLinks.length > 0 && (
                <div className="flex gap-3">
                  {socialLinks.map((link) => (
                    <a
                      key={link.label}
                      href={link.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-muted-foreground/60 hover:text-muted-foreground transition-colors"
                      title={link.label}
                    >
                      {link.icon}
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        </Card>

        {/* Contact Info */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg">Contact Information</CardTitle>
          </CardHeader>
          <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {member.phone && (
              <div>
                <span className="text-sm text-muted-foreground">Phone</span>
                <p className="font-medium">
                  <a
                    href={`tel:${member.phone}`}
                    className="text-accent hover:text-accent/80"
                  >
                    {member.phone}
                  </a>
                </p>
              </div>
            )}
            {member.office_address && (
              <div>
                <span className="text-sm text-muted-foreground">Office</span>
                <p className="font-medium text-foreground/80">
                  {member.office_address}
                </p>
              </div>
            )}
            {member.website_url && (
              <div>
                <span className="text-sm text-muted-foreground">Website</span>
                <p>
                  <a
                    href={member.website_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-accent hover:text-accent/80"
                  >
                    Official Website
                  </a>
                </p>
              </div>
            )}
            {member.contact_url && (
              <div>
                <span className="text-sm text-muted-foreground">Contact Form</span>
                <p>
                  <a
                    href={member.contact_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-accent hover:text-accent/80"
                  >
                    Send a Message
                  </a>
                </p>
              </div>
            )}
          </div>
          </CardContent>
        </Card>

        {/* Bio */}
        {member.ai_bio && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="text-lg">About</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-foreground/80 whitespace-pre-wrap">{member.ai_bio}</p>
              <p className="text-xs text-muted-foreground/60 mt-2">AI-generated biography</p>
            </CardContent>
          </Card>
        )}

        {/* Stats */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg">Legislative Activity</CardTitle>
          </CardHeader>
          <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-4 bg-background rounded-lg">
              <p className="text-3xl font-bold text-foreground">
                {member.sponsored_bills_count}
              </p>
              <p className="text-sm text-muted-foreground">Bills Sponsored</p>
            </div>
            <div className="text-center p-4 bg-background rounded-lg">
              <p className="text-3xl font-bold text-foreground">
                {member.recent_votes.length}
              </p>
              <p className="text-sm text-muted-foreground">Recent Votes</p>
            </div>
          </div>
          </CardContent>
        </Card>

        {/* Recent Votes */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recent Votes</CardTitle>
          </CardHeader>
          <CardContent>
          {member.recent_votes.length > 0 ? (
            <div>
              {member.recent_votes.map((vote) => (
                <RecentVoteItem key={vote.vote_id} vote={vote} />
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-4">
              No recent votes recorded.
            </p>
          )}
          </CardContent>
        </Card>
      </GridContainer>
    </main>
  );
}
