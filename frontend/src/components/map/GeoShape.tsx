"use client";

import { useEffect, useState, useMemo } from "react";
import { geoAlbersUsa, geoPath } from "d3-geo";
import type { GeoPermissibleObjects } from "d3-geo";
import { feature } from "topojson-client";
import type { Topology } from "topojson-specification";

import { FIPS_TO_STATE, STATE_TO_FIPS } from "@/lib/fips";
import { getPartyColor } from "@/lib/utils";
import type { MemberListItem } from "@/types";

const SPLIT_COLOR = "#8B5CF6"; // violet-500 for split-party states
const EMPTY_COLOR = "#d1d5db"; // gray-300

interface StateFeature {
  type: "Feature";
  id: string;
  geometry: GeoPermissibleObjects;
  properties: { name: string };
}

interface DistrictFeature {
  type: "Feature";
  geometry: GeoPermissibleObjects;
  properties: {
    STATEFP: string;
    CD119FP: string;
    GEOID: string;
    NAMELSAD: string;
  };
}

interface GeoShapeProps {
  /** "senate" renders a single state; "house" renders all districts in a state */
  chamber: "senate" | "house";
  stateCode: string;
  /** For house: which district to highlight (others dimmed). null = highlight all. */
  highlightDistrict?: number | null;
  /** Members to derive fill colors from */
  members: MemberListItem[];
  /** CSS view-transition-name for cross-page morph animation */
  viewTransitionName?: string;
  className?: string;
}

export default function GeoShape({
  chamber,
  stateCode,
  highlightDistrict,
  members,
  viewTransitionName,
  className,
}: GeoShapeProps) {
  const [stateFeatures, setStateFeatures] = useState<StateFeature[]>([]);
  const [districtFeatures, setDistrictFeatures] = useState<DistrictFeature[]>(
    []
  );

  const fips = STATE_TO_FIPS[stateCode];

  // Load the appropriate TopoJSON
  useEffect(() => {
    if (chamber === "senate") {
      fetch("/geo/us-states-10m.json")
        .then((r) => r.json())
        .then((topo: Topology) => {
          const fc = feature(topo, topo.objects.states) as unknown as {
            features: StateFeature[];
          };
          setStateFeatures(fc.features.filter((f) => f.id === fips));
        });
    } else {
      fetch("/geo/us-congress-20m.json")
        .then((r) => r.json())
        .then((topo: Topology) => {
          const fc = feature(topo, topo.objects.districts) as unknown as {
            features: DistrictFeature[];
          };
          setDistrictFeatures(
            fc.features.filter((f) => f.properties.STATEFP === fips)
          );
        });
    }
  }, [chamber, fips]);

  // Index members for color lookup
  const membersByDistrict = useMemo(() => {
    const map = new Map<string, MemberListItem>();
    for (const m of members) {
      const key = `${m.state}-${m.district ?? 0}`;
      map.set(key, m);
    }
    return map;
  }, [members]);

  const senatorsByState = useMemo(() => {
    return members.filter((m) => m.state === stateCode);
  }, [members, stateCode]);

  // Determine features and compute projection
  const features =
    chamber === "senate"
      ? (stateFeatures as unknown as GeoPermissibleObjects[])
      : (districtFeatures as unknown as GeoPermissibleObjects[]);

  if (features.length === 0) {
    // Render placeholder SVG with viewTransitionName so browser can pair it
    return (
      <div
        className={className}
        style={viewTransitionName ? { viewTransitionName } : undefined}
      >
        <svg
          viewBox="0 0 960 600"
          className="h-full w-full"
          preserveAspectRatio="xMidYMid meet"
        />
      </div>
    );
  }

  const baseWidth = 960;
  const baseHeight = 600;

  // Use the standard projection, then crop the viewBox to the shape bounds
  const projection = geoAlbersUsa()
    .scale(1280)
    .translate([baseWidth / 2, baseHeight / 2]);
  const pathGenerator = geoPath(projection);

  // Compute bounding box of the features in projected coordinates
  let minX = Infinity,
    minY = Infinity,
    maxX = -Infinity,
    maxY = -Infinity;
  for (const f of features) {
    const bounds = pathGenerator.bounds(f);
    if (bounds) {
      minX = Math.min(minX, bounds[0][0]);
      minY = Math.min(minY, bounds[0][1]);
      maxX = Math.max(maxX, bounds[1][0]);
      maxY = Math.max(maxY, bounds[1][1]);
    }
  }

  // Add padding around the shape (5% of the larger dimension)
  const bw = maxX - minX;
  const bh = maxY - minY;
  const pad = Math.max(bw, bh) * 0.05;
  const vbX = minX - pad;
  const vbY = minY - pad;
  const vbW = bw + pad * 2;
  const vbH = bh + pad * 2;
  const viewBox = isFinite(minX)
    ? `${vbX} ${vbY} ${vbW} ${vbH}`
    : `0 0 ${baseWidth} ${baseHeight}`;

  function getStateColor(): string {
    if (senatorsByState.length === 0) return EMPTY_COLOR;
    const parties = new Set(senatorsByState.map((s) => s.party));
    if (parties.size === 1) return getPartyColor(senatorsByState[0].party);
    return SPLIT_COLOR;
  }

  function getDistrictColor(feat: DistrictFeature): string {
    const sc = FIPS_TO_STATE[feat.properties.STATEFP];
    if (!sc) return EMPTY_COLOR;
    const districtNum = parseInt(feat.properties.CD119FP, 10);
    const member = membersByDistrict.get(`${sc}-${districtNum}`);
    return member ? getPartyColor(member.party) : EMPTY_COLOR;
  }

  return (
    <div
      className={className}
      style={viewTransitionName ? { viewTransitionName } : undefined}
    >
      <svg
        viewBox={viewBox}
        className="h-full w-full"
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label={`Map of ${stateCode}`}
      >
        {chamber === "senate"
          ? stateFeatures.map((feat) => {
              const d = pathGenerator(feat as GeoPermissibleObjects);
              if (!d) return null;
              return (
                <path
                  key={feat.id}
                  d={d}
                  fill={getStateColor()}
                  stroke="#ffffff"
                  strokeWidth={0.5}
                />
              );
            })
          : districtFeatures.map((feat) => {
              const d = pathGenerator(feat as GeoPermissibleObjects);
              if (!d) return null;
              const districtNum = parseInt(feat.properties.CD119FP, 10);
              const isHighlighted =
                highlightDistrict == null ||
                districtNum === highlightDistrict;

              return (
                <path
                  key={feat.properties.GEOID}
                  d={d}
                  fill={getDistrictColor(feat)}
                  stroke="#ffffff"
                  strokeWidth={0.3}
                  opacity={isHighlighted ? 1 : 0.3}
                />
              );
            })}
      </svg>
    </div>
  );
}
