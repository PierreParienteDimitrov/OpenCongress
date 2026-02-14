"use client";

import { Plus, Minus, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface MapZoomControlsProps {
  isZoomed: boolean;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onReset: () => void;
}

export default function MapZoomControls({
  isZoomed,
  onZoomIn,
  onZoomOut,
  onReset,
}: MapZoomControlsProps) {
  return (
    <div className="absolute right-2 top-2 z-10 flex flex-col gap-1">
      <Button
        variant="secondary"
        size="icon"
        className="size-8 cursor-pointer"
        onClick={onZoomIn}
        aria-label="Zoom in"
      >
        <Plus className="size-4" />
      </Button>
      <Button
        variant="secondary"
        size="icon"
        className="size-8 cursor-pointer"
        onClick={onZoomOut}
        aria-label="Zoom out"
      >
        <Minus className="size-4" />
      </Button>
      {isZoomed && (
        <Button
          variant="secondary"
          size="icon"
          className="size-8 cursor-pointer"
          onClick={onReset}
          aria-label="Reset zoom"
        >
          <RotateCcw className="size-3.5" />
        </Button>
      )}
    </div>
  );
}
