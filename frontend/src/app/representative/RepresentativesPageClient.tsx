"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { List, Map } from "lucide-react";

import type { MemberListItem, PaginatedResponse } from "@/types";
import { getRepresentativesPaginated } from "@/lib/api";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import MemberList from "@/components/member/MemberList";
import CongressMap from "@/components/map/CongressMap";

interface RepresentativesPageClientProps {
  initialData: PaginatedResponse<MemberListItem>;
  allMembers: MemberListItem[];
}

export default function RepresentativesPageClient({
  initialData,
  allMembers,
}: RepresentativesPageClientProps) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const currentView = searchParams.get("view") ?? "list";

  function handleTabChange(value: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (value === "list") {
      params.delete("view");
    } else {
      params.set("view", value);
    }
    const query = params.toString();
    router.replace(query ? `?${query}` : ".", { scroll: false });
  }

  return (
    <Tabs value={currentView} onValueChange={handleTabChange}>
      <TabsList>
        <TabsTrigger value="list">
          <List className="mr-1.5 size-4" />
          List
        </TabsTrigger>
        <TabsTrigger value="map">
          <Map className="mr-1.5 size-4" />
          Map
        </TabsTrigger>
      </TabsList>
      <TabsContent value="list">
        <MemberList
          chamber="house"
          initialData={initialData}
          fetchFn={getRepresentativesPaginated}
        />
      </TabsContent>
      <TabsContent value="map">
        <CongressMap members={allMembers} chamber="house" />
      </TabsContent>
    </Tabs>
  );
}
