"use client";

import { useState } from "react";
import { Search, Loader2 } from "lucide-react";

import type { ZipLookupResult } from "@/types";
import { lookupZipCode } from "@/lib/api";

interface ZipCodeSearchProps {
  onResult: (result: ZipLookupResult) => void;
  onClear: () => void;
}

export default function ZipCodeSearch({ onResult, onClear }: ZipCodeSearchProps) {
  const [zip, setZip] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = zip.trim();
    if (!trimmed) return;

    if (!/^\d{5}$/.test(trimmed)) {
      setError("Please enter a valid 5-digit zip code");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await lookupZipCode(trimmed);
      onResult(result);
    } catch {
      setError("Could not find a congressional district for this zip code");
    } finally {
      setLoading(false);
    }
  }

  function handleClear() {
    setZip("");
    setError(null);
    onClear();
  }

  return (
    <div className="mb-4">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            value={zip}
            onChange={(e) => setZip(e.target.value)}
            placeholder="Search by zip code..."
            maxLength={5}
            className="h-10 w-full rounded-md border border-input bg-card pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-2 focus:ring-ring/50"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {loading ? <Loader2 className="size-4 animate-spin" /> : "Search"}
        </button>
        <button
          type="button"
          onClick={handleClear}
          className="inline-flex h-10 items-center justify-center rounded-md border border-input bg-card px-4 text-sm font-medium text-foreground hover:bg-accent"
        >
          Clear
        </button>
      </form>
      {error && (
        <p className="mt-2 text-sm text-glory-red-500 dark:text-glory-red-400">{error}</p>
      )}
    </div>
  );
}
