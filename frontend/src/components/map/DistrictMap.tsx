"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { geoAlbersUsa, geoPath } from "d3-geo";
import type { GeoPermissibleObjects } from "d3-geo";
import { feature } from "topojson-client";
import type { Topology } from "topojson-specification";
import type { MemberListItem } from "@/types";
import { FIPS_TO_STATE } from "@/lib/fips";
import { getPartyColor } from "@/lib/utils";
import { routes } from "@/lib/routes";
import MapTooltip, { type MapTooltipMember } from "./MapTooltip";
import MapZoomControls from "./MapZoomControls";
import { useViewTransitionRouter } from "./useViewTransitionRouter";
import { useMapZoom } from "./useMapZoom";

const EMPTY_COLOR = "#d1d5db"; // gray-300

const WIDTH = 960;
const HEIGHT = 600;

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

export default function DistrictMap({
  members,
  focusedState,
}: DistrictMapProps) {
  const {
    svgRef,
    svgNode,
    gRef,
    transform,
    isZoomed,
    resetZoom,
    zoomIn,
    zoomOut,
    zoomToBounds,
  } = useMapZoom({ width: WIDTH, height: HEIGHT });
  const { push } = useViewTransitionRouter();
  const [features, setFeatures] = useState<DistrictFeature[]>([]);
  const [activeDistrict, setActiveDistrict] = useState<string | null>(null);
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

  // Stable projection and path generator
  const projection = useMemo(
    () => geoAlbersUsa().scale(1280).translate([WIDTH / 2, HEIGHT / 2]),
    []
  );
  const pathGenerator = useMemo(() => geoPath(projection), [projection]);

  // Zoom to focused state or reset
  useEffect(() => {
    if (!focusedState || features.length === 0) {
      if (features.length > 0) resetZoom();
      return;
    }
    const stateFeats = features.filter(
      (f) => FIPS_TO_STATE[f.properties.STATEFP] === focusedState
    );
    if (stateFeats.length === 0) return;

    let minX = Infinity,
      minY = Infinity,
      maxX = -Infinity,
      maxY = -Infinity;
    for (const f of stateFeats) {
      const bounds = pathGenerator.bounds(f as GeoPermissibleObjects);
      if (bounds) {
        minX = Math.min(minX, bounds[0][0]);
        minY = Math.min(minY, bounds[0][1]);
        maxX = Math.max(maxX, bounds[1][0]);
        maxY = Math.max(maxY, bounds[1][1]);
      }
    }
    if (isFinite(minX)) {
      zoomToBounds([
        [minX, minY],
        [maxX, maxY],
      ]);
    }
  }, [focusedState, features, pathGenerator, resetZoom, zoomToBounds]);

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

      const svg = svgNode.current;
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
    [getMemberForDistrict, svgNode]
  );

  const handleClick = useCallback(
    (feat: DistrictFeature, event: React.MouseEvent) => {
      if (event.defaultPrevented) return;
      const stateCode = FIPS_TO_STATE[feat.properties.STATEFP];
      if (!stateCode) return;
      const districtNum = parseInt(feat.properties.CD119FP, 10);
      const districtId = `${stateCode}-${districtNum}`;
      setActiveDistrict(districtId);
      requestAnimationFrame(() => {
        push(routes.house.district(districtId));
      });
    },
    [push]
  );

  const handleMouseLeave = useCallback(() => {
    setTooltip(null);
  }, []);

  if (features.length === 0) return null;

  return (
    <div className="relative h-full">
      <svg
        ref={svgRef}
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        className="h-full w-full cursor-grab touch-none"
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label="US Congressional district map"
      >
        <g ref={gRef}>
          {features.map((feat) => {
            const d = pathGenerator(feat as GeoPermissibleObjects);
            if (!d) return null;
            const stateCode = FIPS_TO_STATE[feat.properties.STATEFP];
            const isHighlighted =
              !focusedState || stateCode === focusedState;

            const districtNum = parseInt(feat.properties.CD119FP, 10);

            return (
              <path
                key={feat.properties.GEOID}
                d={d}
                fill={getDistrictColor(feat)}
                stroke="#ffffff"
                strokeWidth={0.3 / transform.k}
                opacity={isHighlighted ? 1 : 0.2}
                style={
                  activeDistrict === `${stateCode}-${districtNum}`
                    ? { viewTransitionName: `geo-shape` }
                    : undefined
                }
                className="cursor-pointer transition-opacity hover:opacity-80"
                onMouseEnter={(e) => handleMouseEnter(feat, e)}
                onMouseMove={(e) => {
                  const svg = svgNode.current;
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
                onClick={(e) => handleClick(feat, e)}
              />
            );
          })}
        </g>
      </svg>
      {tooltip && <MapTooltip {...tooltip} />}
      <MapZoomControls
        isZoomed={isZoomed}
        onZoomIn={zoomIn}
        onZoomOut={zoomOut}
        onReset={resetZoom}
      />
    </div>
  );
}
