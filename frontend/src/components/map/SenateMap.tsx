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

const SPLIT_COLOR = "#8B5CF6"; // violet-500 for split-party states
const EMPTY_COLOR = "#d1d5db"; // gray-300

const WIDTH = 960;
const HEIGHT = 600;

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
  const [features, setFeatures] = useState<StateFeature[]>([]);
  const [activeState, setActiveState] = useState<string | null>(null);
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
    const stateFeat = features.find(
      (f) => FIPS_TO_STATE[f.id] === focusedState
    );
    if (!stateFeat) return;
    const bounds = pathGenerator.bounds(stateFeat as GeoPermissibleObjects);
    if (bounds) {
      zoomToBounds(bounds);
    }
  }, [focusedState, features, pathGenerator, resetZoom, zoomToBounds]);

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

      const svg = svgNode.current;
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
    [senatorsByState, svgNode]
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
        aria-label="US Senate map by state"
      >
        <g ref={gRef}>
          {features.map((feat) => {
            const d = pathGenerator(feat as GeoPermissibleObjects);
            if (!d) return null;
            const stateCode = FIPS_TO_STATE[feat.id];
            const isHighlighted =
              !focusedState || stateCode === focusedState;

            return (
              <path
                key={feat.id}
                d={d}
                fill={getStateColor(feat.id)}
                stroke="#ffffff"
                strokeWidth={0.5 / transform.k}
                opacity={isHighlighted ? 1 : 0.2}
                style={
                  stateCode && activeState === stateCode
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
                onClick={(e) => {
                  if (e.defaultPrevented) return;
                  if (stateCode) {
                    setActiveState(stateCode);
                    requestAnimationFrame(() => {
                      push(routes.senate.state(stateCode));
                    });
                  }
                }}
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
