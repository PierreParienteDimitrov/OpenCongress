"use client";

import MemberList from "@/components/member/MemberList";
import { getRepresentativesPaginated } from "@/lib/api";
import type { MemberListItem, PaginatedResponse } from "@/types";

interface RepresentativeListProps {
  initialData: PaginatedResponse<MemberListItem>;
}

export default function RepresentativeList({ initialData }: RepresentativeListProps) {
  return (
    <MemberList
      chamber="house"
      initialData={initialData}
      fetchFn={getRepresentativesPaginated}
    />
  );
}
