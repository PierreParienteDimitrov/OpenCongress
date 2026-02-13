"use client";

import { useEffect, useState, useCallback, useRef, useMemo } from "react";
import { geoAlbersUsa, geoPath } from "d3-geo";
import type { GeoPermissibleObjects } from "d3-geo";
import { feature } from "topojson-client";
import type { Topology } from "topojson-specification";
import { useRouter } from "next/navigation";

import type { MemberListItem } from "@/types";
import { FIPS_TO_STATE } from "@/lib/fips";
import { getPartyColor } from "@/lib/utils";
import { getMemberRoute } from "@/lib/routes";
import MapTooltip, { type MapTooltipMember } from "./MapTooltip";

const EMPTY_COLOR = "#d1d5db"; // gray-300

interface DistrictMapProps {
  members: MemberListItem[];
  focusedState?: string | null;
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

export default function DistrictMap({ members, focusedState }: DistrictMapProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const router = useRouter();
  const [features, setFeatures] = useState<DistrictFeature[]>([]);
  const [tooltip, setTooltip] = useState<{
    x: number;
    y: number;
    members: MapTooltipMember[];
  } | null>(null);

  // Index members by state+district
  const membersByDistrict = useMemo(() => {
    const map = new Map<string, MemberListItem>();
    for (const m of members) {
      const key = `${m.state}-${m.district ?? 0}`;
      map.set(key, m);
    }
    return map;
  }, [members]);

  // Load TopoJSON
  useEffect(() => {
    fetch("/geo/us-congress-20m.json")
      .then((r) => r.json())
      .then((topo: Topology) => {
        const fc = feature(topo, topo.objects.districts) as unknown as {
          features: DistrictFeature[];
        };
        setFeatures(fc.features);
      });
  }, []);

  const getMemberForDistrict = useCallback(
    (feat: DistrictFeature): MemberListItem | undefined => {
      const stateCode = FIPS_TO_STATE[feat.properties.STATEFP];
      if (!stateCode) return undefined;
      const districtNum = parseInt(feat.properties.CD119FP, 10);
      return membersByDistrict.get(`${stateCode}-${districtNum}`);
    },
    [membersByDistrict]
  );

  const getDistrictColor = useCallback(
    (feat: DistrictFeature): string => {
      const member = getMemberForDistrict(feat);
      return member ? getPartyColor(member.party) : EMPTY_COLOR;
    },
    [getMemberForDistrict]
  );

  const handleMouseEnter = useCallback(
    (feat: DistrictFeature, event: React.MouseEvent) => {
      const member = getMemberForDistrict(feat);
      if (!member) return;

      const svg = svgRef.current;
      if (!svg) return;
      const rect = svg.getBoundingClientRect();

      setTooltip({
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
        members: [
          {
            name: member.full_name,
            party: member.party,
            state: member.state,
            district: member.district,
            chamber: "house" as const,
            bioguideId: member.bioguide_id,
          },
        ],
      });
    },
    [getMemberForDistrict]
  );

  const handleClick = useCallback(
    (feat: DistrictFeature) => {
      const member = getMemberForDistrict(feat);
      if (member) {
        router.push(getMemberRoute(member.bioguide_id, "house"));
      }
    },
    [getMemberForDistrict, router]
  );

  const handleMouseLeave = useCallback(() => {
    setTooltip(null);
  }, []);

  if (features.length === 0) return null;

  const width = 960;
  const height = 600;

  let projection = geoAlbersUsa().scale(1280).translate([width / 2, height / 2]);

  if (focusedState) {
    // Filter to just the focused state's districts and fit projection
    const stateFeats = features.filter(
      (f) => FIPS_TO_STATE[f.properties.STATEFP] === focusedState
    );
    if (stateFeats.length > 0) {
      const tempProjection = geoAlbersUsa()
        .scale(1280)
        .translate([width / 2, height / 2]);
      const tempPath = geoPath(tempProjection);

      // Compute combined bounds across all district features of the state
      let minX = Infinity,
        minY = Infinity,
        maxX = -Infinity,
        maxY = -Infinity;
      for (const f of stateFeats) {
        const bounds = tempPath.bounds(f as GeoPermissibleObjects);
        if (bounds) {
          minX = Math.min(minX, bounds[0][0]);
          minY = Math.min(minY, bounds[0][1]);
          maxX = Math.max(maxX, bounds[1][0]);
          maxY = Math.max(maxY, bounds[1][1]);
        }
      }

      if (isFinite(minX)) {
        const bw = maxX - minX;
        const bh = maxY - minY;
        const scale = (0.8 / Math.max(bw / width, bh / height)) * 1280;
        const cx = (minX + maxX) / 2;
        const cy = (minY + maxY) / 2;
        projection = geoAlbersUsa()
          .scale(scale)
          .translate([
            width / 2 - cx * (scale / 1280) + width / 2,
            height / 2 - cy * (scale / 1280) + height / 2,
          ]);
      }
    }
  }

  const pathGenerator = geoPath(projection);

  return (
    <div className="relative">
      <svg
        ref={svgRef}
        viewBox={`0 0 ${width} ${height}`}
        className="h-full w-full"
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label="US Congressional district map"
      >
        {features.map((feat) => {
          const d = pathGenerator(feat as GeoPermissibleObjects);
          if (!d) return null;
          const stateCode = FIPS_TO_STATE[feat.properties.STATEFP];
          const isHighlighted = !focusedState || stateCode === focusedState;

          return (
            <path
              key={feat.properties.GEOID}
              d={d}
              fill={getDistrictColor(feat)}
              stroke="#ffffff"
              strokeWidth={0.3}
              opacity={isHighlighted ? 1 : 0.2}
              className="cursor-pointer transition-opacity hover:opacity-80"
              onMouseEnter={(e) => handleMouseEnter(feat, e)}
              onMouseMove={(e) => {
                const svg = svgRef.current;
                if (!svg) return;
                const rect = svg.getBoundingClientRect();
                setTooltip((prev) =>
                  prev
                    ? {
                        ...prev,
                        x: e.clientX - rect.left,
                        y: e.clientY - rect.top,
                      }
                    : null
                );
              }}
              onMouseLeave={handleMouseLeave}
              onClick={() => handleClick(feat)}
            />
          );
        })}
      </svg>
      {tooltip && <MapTooltip {...tooltip} />}
    </div>
  );
}
