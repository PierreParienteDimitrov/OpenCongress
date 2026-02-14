"use client";

import { useRef, useCallback, useState } from "react";
import { zoom, zoomIdentity } from "d3-zoom";
import { select } from "d3-selection";
import "d3-transition";
import type { ZoomTransform, ZoomBehavior } from "d3-zoom";

interface UseMapZoomOptions {
  width: number;
  height: number;
  minZoom?: number;
  maxZoom?: number;
  transitionDuration?: number;
}

interface UseMapZoomReturn {
  /** Callback ref — pass to <svg ref={svgRef}> */
  svgRef: (node: SVGSVGElement | null) => void;
  /** Stable ref to the SVG node for reading (e.g. getBoundingClientRect) */
  svgNode: React.RefObject<SVGSVGElement | null>;
  gRef: React.RefObject<SVGGElement | null>;
  transform: ZoomTransform;
  isZoomed: boolean;
  resetZoom: () => void;
  zoomIn: () => void;
  zoomOut: () => void;
  zoomToBounds: (bounds: [[number, number], [number, number]]) => void;
}

export function useMapZoom({
  width,
  height,
  minZoom = 1,
  maxZoom = 8,
  transitionDuration = 750,
}: UseMapZoomOptions): UseMapZoomReturn {
  const svgNodeRef = useRef<SVGSVGElement | null>(null);
  const gRef = useRef<SVGGElement>(null);
  const zoomBehaviorRef = useRef<ZoomBehavior<SVGSVGElement, unknown> | null>(
    null
  );
  const [currentTransform, setCurrentTransform] =
    useState<ZoomTransform>(zoomIdentity);

  // Callback ref: called when SVG mounts/unmounts.
  // This guarantees we attach d3-zoom only when the SVG is in the DOM.
  const svgRef = useCallback(
    (node: SVGSVGElement | null) => {
      // Cleanup previous
      if (svgNodeRef.current) {
        select(svgNodeRef.current).on(".zoom", null);
        svgNodeRef.current.removeEventListener("wheel", preventDefault);
        svgNodeRef.current.removeEventListener(
          "gesturestart",
          preventDefault
        );
        svgNodeRef.current.removeEventListener(
          "gesturechange",
          preventDefault
        );
        zoomBehaviorRef.current = null;
      }

      svgNodeRef.current = node;
      if (!node) return;

      const zoomBehavior = zoom<SVGSVGElement, unknown>()
        .scaleExtent([minZoom, maxZoom])
        .translateExtent([
          [0, 0],
          [width, height],
        ])
        .on("zoom", (event) => {
          const g = gRef.current;
          if (g) {
            const t = event.transform;
            g.setAttribute(
              "transform",
              `translate(${t.x},${t.y}) scale(${t.k})`
            );
          }
          setCurrentTransform(event.transform);
        });

      zoomBehaviorRef.current = zoomBehavior;
      select(node).call(zoomBehavior);

      // Prevent browser from intercepting wheel/pinch as native page zoom
      node.addEventListener("wheel", preventDefault, { passive: false });
      node.addEventListener("gesturestart", preventDefault);
      node.addEventListener("gesturechange", preventDefault);
    },
    [width, height, minZoom, maxZoom]
  );

  const resetZoom = useCallback(() => {
    const svg = svgNodeRef.current;
    const zb = zoomBehaviorRef.current;
    if (!svg || !zb) return;
    select(svg)
      .transition()
      .duration(transitionDuration)
      .call(zb.transform, zoomIdentity);
  }, [transitionDuration]);

  const zoomIn = useCallback(() => {
    const svg = svgNodeRef.current;
    const zb = zoomBehaviorRef.current;
    if (!svg || !zb) return;
    select(svg).transition().duration(300).call(zb.scaleBy, 2);
  }, []);

  const zoomOut = useCallback(() => {
    const svg = svgNodeRef.current;
    const zb = zoomBehaviorRef.current;
    if (!svg || !zb) return;
    select(svg).transition().duration(300).call(zb.scaleBy, 0.5);
  }, []);

  const zoomToBounds = useCallback(
    (bounds: [[number, number], [number, number]]) => {
      const svg = svgNodeRef.current;
      const zb = zoomBehaviorRef.current;
      if (!svg || !zb) return;

      const [[x0, y0], [x1, y1]] = bounds;
      const bw = x1 - x0;
      const bh = y1 - y0;
      const padding = 0.1;
      const scale = (1 - padding) / Math.max(bw / width, bh / height);
      const cx = (x0 + x1) / 2;
      const cy = (y0 + y1) / 2;

      const targetTransform = zoomIdentity
        .translate(width / 2, height / 2)
        .scale(Math.min(scale, maxZoom))
        .translate(-cx, -cy);

      select(svg)
        .transition()
        .duration(transitionDuration)
        .call(zb.transform, targetTransform);
    },
    [width, height, maxZoom, transitionDuration]
  );

  const isZoomed = currentTransform.k > 1.01;

  return {
    svgRef,
    svgNode: svgNodeRef,
    gRef,
    transform: currentTransform,
    isZoomed,
    resetZoom,
    zoomIn,
    zoomOut,
    zoomToBounds,
  };
}

function preventDefault(e: Event) {
  e.preventDefault();
}
