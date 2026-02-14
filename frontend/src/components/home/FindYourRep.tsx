"use client";

import { useState } from "react";
import Link from "next/link";

import ZipCodeSearch from "@/components/map/ZipCodeSearch";
import { Badge } from "@/components/ui/badge";
import type { ZipLookupResult } from "@/types";
import { cn, getPartyBgColor, getPartyName } from "@/lib/utils";
import { getMemberRoute } from "@/lib/routes";

export default function FindYourRep() {
  const [result, setResult] = useState<ZipLookupResult | null>(null);

  return (
    <div>
      <ZipCodeSearch onResult={setResult} onClear={() => setResult(null)} />
      {result && result.members.length > 0 && (
        <div className="mt-3 space-y-2">
          {result.members.map((member) => (
            <Link
              key={member.bioguide_id}
              href={getMemberRoute(member.bioguide_id, member.chamber)}
              className="flex items-center gap-3 cursor-pointer rounded border border-border bg-card p-3 transition-all hover:border-muted-foreground/30 hover:shadow-sm"
            >
              <img
                src={member.photo_url}
                alt={member.full_name}
                className="h-10 w-10 rounded-full object-cover"
                loading="lazy"
              />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-foreground">
                  {member.full_name}
                </p>
                <div className="mt-1 flex items-center gap-2">
                  <Badge className={cn("text-xs", getPartyBgColor(member.party))}>
                    {getPartyName(member.party)}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {member.chamber === "senate" ? "Senator" : "Representative"}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
