"use client";

import { useSession } from "next-auth/react";
import { useQuery } from "@tanstack/react-query";
import Image from "next/image";
import Link from "next/link";
import { fetchMyRepresentatives } from "@/lib/api-client";
import { routes } from "@/lib/routes";
import { cn, getPartyBgColor } from "@/lib/utils";

export function NavRepAvatars() {
  const { data: session } = useSession();

  const { data } = useQuery({
    queryKey: ["my-representatives"],
    queryFn: fetchMyRepresentatives,
    enabled: !!session,
    staleTime: 5 * 60 * 1000,
  });

  const members = data?.followed_members?.slice(0, 3);

  if (!members || members.length === 0) return null;

  return (
    <Link
      href={routes.settings.representatives}
      className="hidden lg:flex items-center cursor-pointer"
      title="Your representatives"
    >
      <div className="flex -space-x-2">
        {members.map((member) => (
          <div
            key={member.bioguide_id}
            className={cn(
              "relative size-7 rounded-full ring-2 ring-nav overflow-hidden",
              getPartyBgColor(member.party),
            )}
          >
            <Image
              src={member.photo_url}
              alt={member.full_name}
              width={28}
              height={28}
              className="rounded-full object-cover size-7"
            />
          </div>
        ))}
      </div>
    </Link>
  );
}
