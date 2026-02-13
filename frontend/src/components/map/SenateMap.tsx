"use client";

import { useEffect, useState, useCallback, useRef, useMemo } from "react";
import { geoAlbersUsa, geoPath } from "d3-geo";
import type { GeoPermissibleObjects } from "d3-geo";
import { feature } from "topojson-client";
import type { Topology } from "topojson-specification";

import type { MemberListItem } from "@/types";
import { FIPS_TO_STATE } from "@/lib/fips";
import { getPartyColor } from "@/lib/utils";
import { routes } from "@/lib/routes";
import MapTooltip, { type MapTooltipMember } from "./MapTooltip";
import { useViewTransitionRouter } from "./useViewTransitionRouter";

const SPLIT_COLOR = "#8B5CF6"; // violet-500 for split-party states
const EMPTY_COLOR = "#d1d5db"; // gray-300

interface SenateMapProps {
  members: MemberListItem[];
  focusedState?: string | null;
}

interface StateFeature {
  type: "Feature";
  id: string;
  geometry: GeoPermissibleObjects;
  properties: { name: string };
}

export default function SenateMap({ members, focusedState }: SenateMapProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const { push } = useViewTransitionRouter();
  const [features, setFeatures] = useState<StateFeature[]>([]);
  const [tooltip, setTooltip] = useState<{
    x: number;
    y: number;
    members: MapTooltipMember[];
  } | null>(null);

  // Index senators by state
  const senatorsByState = useMemo(() => {
    const map = new Map<string, MemberListItem[]>();
    for (const m of members) {
      const list = map.get(m.state) ?? [];
      list.push(m);
      map.set(m.state, list);
    }
    return map;
  }, [members]);

  // Load TopoJSON
  useEffect(() => {
    fetch("/geo/us-states-10m.json")
      .then((r) => r.json())
      .then((topo: Topology) => {
        const fc = feature(topo, topo.objects.states) as unknown as {
          features: StateFeature[];
        };
        setFeatures(fc.features);
      });
  }, []);

  const getStateColor = useCallback(
    (fips: string): string => {
      const stateCode = FIPS_TO_STATE[fips];
      if (!stateCode) return EMPTY_COLOR;
      const senators = senatorsByState.get(stateCode);
      if (!senators || senators.length === 0) return EMPTY_COLOR;

      const parties = new Set(senators.map((s) => s.party));
      if (parties.size === 1) {
        return getPartyColor(senators[0].party);
      }
      return SPLIT_COLOR;
    },
    [senatorsByState]
  );

  const handleMouseEnter = useCallback(
    (feat: StateFeature, event: React.MouseEvent) => {
      const stateCode = FIPS_TO_STATE[feat.id];
      if (!stateCode) return;
      const senators = senatorsByState.get(stateCode);
      if (!senators || senators.length === 0) return;

      const svg = svgRef.current;
      if (!svg) return;
      const rect = svg.getBoundingClientRect();

      setTooltip({
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
        members: senators.map((s) => ({
          name: s.full_name,
          party: s.party,
          state: s.state,
          district: s.district,
          chamber: "senate" as const,
          bioguideId: s.bioguide_id,
        })),
      });
    },
    [senatorsByState]
  );

  const handleMouseLeave = useCallback(() => {
    setTooltip(null);
  }, []);

  if (features.length === 0) return null;

  // Determine projection: default full US, or zoom to a specific state
  const width = 960;
  const height = 600;

  let projection = geoAlbersUsa().scale(1280).translate([width / 2, height / 2]);

  if (focusedState) {
    // Find the focused state feature and fit the projection to it
    const stateFeat = features.find(
      (f) => FIPS_TO_STATE[f.id] === focusedState
    );
    if (stateFeat) {
      const tempProjection = geoAlbersUsa()
        .scale(1280)
        .translate([width / 2, height / 2]);
      const tempPath = geoPath(tempProjection);
      const bounds = tempPath.bounds(stateFeat as GeoPermissibleObjects);
      if (bounds) {
        const [[x0, y0], [x1, y1]] = bounds;
        const bw = x1 - x0;
        const bh = y1 - y0;
        const scale =
          0.8 / Math.max(bw / width, bh / height) * 1280;
        const cx = (x0 + x1) / 2;
        const cy = (y0 + y1) / 2;
        projection = geoAlbersUsa()
          .scale(scale)
          .translate([width / 2 - cx * (scale / 1280) + width / 2, height / 2 - cy * (scale / 1280) + height / 2]);
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
        aria-label="US Senate map by state"
      >
        {features.map((feat) => {
          const d = pathGenerator(feat as GeoPermissibleObjects);
          if (!d) return null;
          const stateCode = FIPS_TO_STATE[feat.id];
          const isHighlighted = !focusedState || stateCode === focusedState;

          return (
            <path
              key={feat.id}
              d={d}
              fill={getStateColor(feat.id)}
              stroke="#ffffff"
              strokeWidth={0.5}
              opacity={isHighlighted ? 1 : 0.2}
              style={
                stateCode
                  ? { viewTransitionName: `state-${stateCode}` }
                  : undefined
              }
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
              onClick={() => {
                if (stateCode) {
                  push(routes.senate.state(stateCode));
                }
              }}
            />
          );
        })}
      </svg>
      {tooltip && <MapTooltip {...tooltip} />}
    </div>
  );
}
