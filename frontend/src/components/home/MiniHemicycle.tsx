"use client";

import dynamic from "next/dynamic";
import type { Seat } from "@/types";
import { Skeleton } from "@/components/ui/skeleton";

const HemicycleChart = dynamic(
  () => import("@/components/hemicycle/HemicycleChart"),
  {
    ssr: false,
    loading: () => <Skeleton className="h-[200px] w-full bg-secondary" />,
  }
);

interface MiniHemicycleProps {
  seats: Seat[];
}

export default function MiniHemicycle({ seats }: MiniHemicycleProps) {
  return (
    <div className="h-[200px] w-full">
      <HemicycleChart chamber="senate" seats={seats} showVoteOverlay={false} />
    </div>
  );
}
