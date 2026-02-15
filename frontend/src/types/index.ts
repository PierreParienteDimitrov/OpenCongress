/**
 * TypeScript types for Congress data matching API responses.
 */

// Member types
export interface MemberListItem {
  bioguide_id: string;
  full_name: string;
  party: "D" | "R" | "I";
  chamber: "house" | "senate";
  state: string;
  district: number | null;
  photo_url: string;
}

export interface MemberRecentVote {
  vote_id: string;
  date: string;
  question: string;
  description: string;
  result: VoteResult;
  position: VotePosition;
  bill_id: string | null;
  bill_display_number: string | null;
}

export interface MemberDetail extends MemberListItem {
  first_name: string;
  last_name: string;
  phone: string;
  office_address: string;
  website_url: string;
  contact_url: string;
  twitter_handle: string;
  facebook_id: string;
  youtube_id: string;
  ai_bio: string;
  term_start: string | null;
  term_end: string | null;
  is_active: boolean;
  recent_votes: MemberRecentVote[];
  sponsored_bills_count: number;
}

// Rep weekly activity types (for "Your Reps This Week" module)
export interface RepSponsoredBillActivity {
  bill_id: string;
  display_number: string;
  short_title: string;
  latest_action_date: string | null;
  latest_action_text: string;
}

export interface RepWeeklyActivity {
  bioguide_id: string;
  full_name: string;
  party: "D" | "R" | "I";
  chamber: "house" | "senate";
  state: string;
  district: number | null;
  photo_url: string;
  recent_votes: MemberRecentVote[];
  sponsored_bills: RepSponsoredBillActivity[];
}

export interface RepActivityResponse {
  members: RepWeeklyActivity[];
}

// Bill types
export interface BillListItem {
  bill_id: string;
  display_number: string;
  bill_type: BillType;
  short_title: string;
  title: string;
  sponsor_name: string | null;
  sponsor_id: string | null;
  introduced_date: string | null;
  latest_action_date: string | null;
  latest_action_text: string;
  has_vote: boolean;
}

export interface BillDetail {
  bill_id: string;
  display_number: string;
  bill_type: BillType;
  number: number;
  congress: number;
  title: string;
  short_title: string;
  summary_text: string;
  summary_html: string;
  ai_summary: string;
  sponsor: MemberListItem | null;
  introduced_date: string | null;
  latest_action_date: string | null;
  latest_action_text: string;
  congress_url: string;
  votes: VoteSummary[];
}

export type BillType =
  | "hr"
  | "s"
  | "hjres"
  | "sjres"
  | "hconres"
  | "sconres"
  | "hres"
  | "sres";

// Vote types
export type VoteResult = "passed" | "failed" | "agreed" | "rejected";
export type VotePosition = "yea" | "nay" | "present" | "not_voting";

export interface VoteSummary {
  vote_id: string;
  chamber: "house" | "senate";
  date: string;
  time: string | null;
  question: string;
  result: VoteResult;
  total_yea: number;
  total_nay: number;
  total_present: number;
  total_not_voting: number;
  dem_yea: number;
  dem_nay: number;
  rep_yea: number;
  rep_nay: number;
  ind_yea: number;
  ind_nay: number;
  is_bipartisan: boolean;
  ai_summary: string;
  bill_id: string | null;
  bill_display_number: string | null;
  bill_short_title: string | null;
  bill_title: string | null;
}

export interface VoteCalendarItem {
  vote_id: string;
  chamber: "house" | "senate";
  date: string;
  time: string | null;
  question: string;
  description: string;
  result: VoteResult;
  total_yea: number;
  total_nay: number;
  bill: string | null;
  bill_display_number: string | null;
  bill_short_title: string | null;
  is_bipartisan: boolean;
}

export interface BillCalendarItem {
  bill_id: string;
  display_number: string;
  short_title: string;
  sponsor_name: string | null;
  sponsor_id: string | null;
  latest_action_date: string | null;
  latest_action_text: string;
}

// Weekly summary types
export type WeeklySummaryType = "recap" | "preview";

export interface WeeklySummary {
  id: number;
  year: number;
  week_number: number;
  summary_type: WeeklySummaryType;
  summary_type_display: string;
  content: string;
  model_used: string;
  prompt_version: string;
  tokens_used: number;
  votes_included: string[];
  bills_included: string[];
  created_at: string;
}

export interface WeeklySummaryListItem {
  id: number;
  year: number;
  week_number: number;
  summary_type: WeeklySummaryType;
  summary_type_display: string;
  created_at: string;
}

// Daily summary types
export type DailySummaryType = "recap" | "preview";

export interface DailySummary {
  id: number;
  date: string;
  summary_type: DailySummaryType;
  summary_type_display: string;
  content: string;
  model_used: string;
  prompt_version: string;
  tokens_used: number;
  votes_included: string[];
  bills_included: string[];
  created_at: string;
}

// Seat types (for hemicycle visualization)
export interface SeatMember {
  bioguide_id: string;
  full_name: string;
  party: "D" | "R" | "I";
  state: string;
  district: number | null;
  photo_url: string;
}

export interface Seat {
  seat_id: string;
  chamber: "house" | "senate";
  section: "democrat" | "republican" | "independent";
  row: number;
  position: number;
  svg_x: number;
  svg_y: number;
  member: SeatMember | null;
}

export interface SeatWithVote extends Seat {
  vote_position: VotePosition | null;
}

// Zip code lookup types
export interface ZipLookupResult {
  state: string;
  state_name: string;
  district: number | null;
  members: MemberListItem[];
}

// Committee types
export interface CommitteeLeader {
  bioguide_id: string;
  full_name: string;
  party: string;
}

export interface CommitteeMemberItem {
  bioguide_id: string;
  full_name: string;
  party: "D" | "R" | "I";
  state: string;
  district: number | null;
  photo_url: string;
  role: string;
  role_display: string;
}

export interface CommitteeListItem {
  committee_id: string;
  name: string;
  chamber: "house" | "senate";
  committee_type: string;
  url: string;
  parent_committee_id: string | null;
  member_count: number;
  subcommittee_count: number;
  chair: CommitteeLeader | null;
  ranking_member: CommitteeLeader | null;
  referred_bills_count: number;
}

export interface CommitteeDetail extends CommitteeListItem {
  ai_summary: string;
  members: CommitteeMemberItem[];
  subcommittees: CommitteeListItem[];
  referred_bills: BillListItem[];
}

// API response types
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
