"use client";

import { ArrowLeft, Users, CalendarDays } from "lucide-react";
import { motion } from "framer-motion";

import type { MemberListItem } from "@/types";
import { getStateName } from "@/lib/utils";
import { routes } from "@/lib/routes";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { GridContainer } from "@/components/layout/GridContainer";
import MapMemberCard from "./MapMemberCard";
import GeoShape from "./GeoShape";
import { useViewTransitionRouter } from "./useViewTransitionRouter";

interface DistrictDetailClientProps {
  stateCode: string;
  districtNum: number;
  /** All representatives for this state (for district coloring) */
  stateMembers: MemberListItem[];
  /** The specific representative for the clicked district */
  representative: MemberListItem | null;
}

export default function DistrictDetailClient({
  stateCode,
  districtNum,
  stateMembers,
  representative,
}: DistrictDetailClientProps) {
  const { push } = useViewTransitionRouter();
  const stateName = getStateName(stateCode);
  const districtLabel =
    districtNum === 0
      ? `${stateName} (At-Large)`
      : `${stateName}, District ${districtNum}`;

  return (
    <main className="min-h-screen bg-background">
      <GridContainer className="py-4">
        {/* Back button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => push(`${routes.house.index}?view=map`)}
          className="mb-4"
        >
          <ArrowLeft className="mr-1 size-4" />
          Back to map
        </Button>

        {/* Title */}
        <h1 className="mb-1 text-2xl font-bold text-foreground sm:text-3xl">
          {districtLabel}
        </h1>
        <p className="mb-6 text-sm text-muted-foreground">
          U.S. House of Representatives
        </p>

        {/* Two-column layout */}
        <div className="grid gap-8 md:grid-cols-12">
          {/* Left: District shape (full state, clicked district highlighted) */}
          <div className="md:col-span-7">
            <GeoShape
              chamber="house"
              stateCode={stateCode}
              highlightDistrict={districtNum}
              members={stateMembers}
              viewTransitionName={`district-${stateCode}-${districtNum}`}
              className="w-full"
            />
          </div>

          {/* Right: Metadata sidebar */}
          <motion.div
            className="md:col-span-5"
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2, duration: 0.4, ease: "easeOut" }}
          >
            {/* Representative */}
            <h2 className="mb-3 text-lg font-semibold text-foreground">
              Representative
            </h2>
            <div className="grid gap-3">
              {representative ? (
                <MapMemberCard member={representative} />
              ) : (
                <p className="text-sm text-muted-foreground">
                  No representative data available.
                </p>
              )}
            </div>

            <Separator className="my-6" />

            {/* Placeholder metadata */}
            <h2 className="mb-3 text-lg font-semibold text-foreground">
              District Info
            </h2>
            <div className="grid gap-3">
              <Card>
                <CardContent className="flex items-center gap-3 py-3">
                  <Users className="size-5 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Population</p>
                    <p className="font-medium text-foreground">Coming soon</p>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="flex items-center gap-3 py-3">
                  <CalendarDays className="size-5 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">
                      Next Election
                    </p>
                    <p className="font-medium text-foreground">
                      November 2026
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </motion.div>
        </div>
      </GridContainer>
    </main>
  );
}
