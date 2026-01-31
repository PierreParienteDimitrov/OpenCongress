"use client";

import MemberList from "@/components/member/MemberList";
import { getSenatorsPaginated } from "@/lib/api";
import type { MemberListItem, PaginatedResponse } from "@/types";

interface SenatorListProps {
  initialData: PaginatedResponse<MemberListItem>;
}

export default function SenatorList({ initialData }: SenatorListProps) {
  return (
    <MemberList
      chamber="senate"
      initialData={initialData}
      fetchFn={getSenatorsPaginated}
    />
  );
}
