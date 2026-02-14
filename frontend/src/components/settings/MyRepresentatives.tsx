"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { MapPin, Loader2, Unlink, Search } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  fetchMyRepresentatives,
  saveMyRepresentatives,
  clearMyRepresentatives,
} from "@/lib/api-client";
import type {
  MyRepresentativesResponse,
  MultipleDistrictsResponse,
} from "@/lib/api-client";
import { lookupZipCode } from "@/lib/api";
import { cn, getPartyBgColor, getPartyName } from "@/lib/utils";
import { getMemberRoute } from "@/lib/routes";
import type { ZipLookupResult, MemberListItem } from "@/types";

function isMultipleDistricts(
  resp: MyRepresentativesResponse | MultipleDistrictsResponse,
): resp is MultipleDistrictsResponse {
  return "multiple_districts" in resp && resp.multiple_districts === true;
}

function RepCard({ member }: { member: MemberListItem }) {
  return (
    <Link
      href={getMemberRoute(member.bioguide_id, member.chamber)}
      className="flex items-center gap-3 cursor-pointer rounded border border-border bg-card p-3 transition-all hover:border-muted-foreground/30 hover:shadow-sm"
    >
      <Image
        src={member.photo_url}
        alt={member.full_name}
        width={40}
        height={40}
        className="h-10 w-10 rounded-full object-cover"
      />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold text-foreground">
          {member.full_name}
        </p>
        <div className="mt-1 flex items-center gap-2">
          <Badge className={cn("text-xs", getPartyBgColor(member.party))}>
            {getPartyName(member.party)}
          </Badge>
          <span className="text-xs text-muted-foreground">
            {member.chamber === "senate" ? "Senator" : "Representative"}
          </span>
        </div>
      </div>
    </Link>
  );
}

export function MyRepresentatives() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["my-representatives"],
    queryFn: fetchMyRepresentatives,
  });

  const saveMutation = useMutation({
    mutationFn: ({
      zipCode,
      district,
    }: {
      zipCode: string;
      district?: number;
    }) => saveMyRepresentatives(zipCode, district),
    onSuccess: (resp) => {
      if (!isMultipleDistricts(resp)) {
        queryClient.invalidateQueries({ queryKey: ["my-representatives"] });
      }
    },
  });

  const clearMutation = useMutation({
    mutationFn: clearMyRepresentatives,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-representatives"] });
      setSearchResult(null);
      setMultiDistricts(null);
      setSelectedDistrict(undefined);
      setZip("");
    },
  });

  // Search state
  const [zip, setZip] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchResult, setSearchResult] = useState<ZipLookupResult | null>(
    null,
  );
  const [multiDistricts, setMultiDistricts] = useState<{
    districts: number[];
    state: string;
    state_name: string;
  } | null>(null);
  const [selectedDistrict, setSelectedDistrict] = useState<
    number | undefined
  >();

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = zip.trim();
    if (!trimmed) return;

    if (!/^\d{5}$/.test(trimmed)) {
      setSearchError("Please enter a valid 5-digit zip code");
      return;
    }

    setSearching(true);
    setSearchError(null);
    setMultiDistricts(null);
    setSelectedDistrict(undefined);

    try {
      const result = await lookupZipCode(trimmed);
      setSearchResult(result);
    } catch {
      setSearchError(
        "Could not find a congressional district for this zip code",
      );
    } finally {
      setSearching(false);
    }
  }

  function handleClear() {
    setZip("");
    setSearchError(null);
    setSearchResult(null);
    setMultiDistricts(null);
    setSelectedDistrict(undefined);
  }

  async function handleSave() {
    const trimmed = zip.trim();
    if (!trimmed) return;

    const resp = await saveMutation.mutateAsync({
      zipCode: trimmed,
      district: selectedDistrict,
    });

    if (isMultipleDistricts(resp)) {
      setMultiDistricts({
        districts: resp.districts,
        state: resp.state,
        state_name: resp.state_name,
      });
      setSearchResult(null);
    }
  }

  if (isLoading) {
    return (
      <Card className="py-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="size-5" />
            My Representatives
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Loading...
          </div>
        </CardContent>
      </Card>
    );
  }

  // Display mode — user has saved reps
  if (data?.has_representatives) {
    return (
      <Card className="py-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="size-5" />
            My Representatives
          </CardTitle>
          <CardDescription>
            {data.state_name}
            {data.district ? `, District ${data.district}` : ""}
            {data.zip_code ? ` (zip: ${data.zip_code})` : ""}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            {data.representatives.map((member) => (
              <RepCard key={member.bioguide_id} member={member} />
            ))}
          </div>
          <Button
            variant="outline"
            onClick={() => clearMutation.mutate()}
            disabled={clearMutation.isPending}
            className="cursor-pointer"
          >
            {clearMutation.isPending ? (
              <Loader2 className="mr-2 size-4 animate-spin" />
            ) : (
              <Unlink className="mr-2 size-4" />
            )}
            Unlink Representatives
          </Button>
        </CardContent>
      </Card>
    );
  }

  // Search mode — no saved reps
  return (
    <Card className="py-4">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MapPin className="size-5" />
          My Representatives
        </CardTitle>
        <CardDescription>
          Enter your zip code to find and save your congressional
          representatives. Saved representatives will be used for your
          personalized feed and notifications.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Zip code search */}
        <form onSubmit={handleSearch} className="flex gap-2">
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
            disabled={searching}
            className="inline-flex h-10 cursor-pointer items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {searching ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              "Search"
            )}
          </button>
          <button
            type="button"
            onClick={handleClear}
            className="inline-flex h-10 cursor-pointer items-center justify-center rounded-md border border-input bg-card px-4 text-sm font-medium text-foreground hover:bg-accent"
          >
            Clear
          </button>
        </form>
        {searchError && (
          <p className="text-sm text-red-600 dark:text-red-400">
            {searchError}
          </p>
        )}

        {/* Multi-district picker */}
        {multiDistricts && (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              This zip code spans multiple congressional districts in{" "}
              {multiDistricts.state_name}. Please select your district:
            </p>
            <Select
              onValueChange={(val) => setSelectedDistrict(Number(val))}
              value={selectedDistrict?.toString()}
            >
              <SelectTrigger className="w-48 cursor-pointer">
                <SelectValue placeholder="Select district" />
              </SelectTrigger>
              <SelectContent>
                {multiDistricts.districts.map((d) => (
                  <SelectItem
                    key={d}
                    value={d.toString()}
                    className="cursor-pointer"
                  >
                    {multiDistricts.state} District {d}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              onClick={handleSave}
              disabled={
                selectedDistrict === undefined || saveMutation.isPending
              }
              className="cursor-pointer"
            >
              {saveMutation.isPending && (
                <Loader2 className="mr-2 size-4 animate-spin" />
              )}
              Save These Representatives
            </Button>
          </div>
        )}

        {/* Search results */}
        {searchResult && searchResult.members.length > 0 && !multiDistricts && (
          <div className="space-y-3">
            <div className="space-y-2">
              {searchResult.members.map((member) => (
                <RepCard key={member.bioguide_id} member={member} />
              ))}
            </div>
            <Button
              onClick={handleSave}
              disabled={saveMutation.isPending}
              className="cursor-pointer"
            >
              {saveMutation.isPending && (
                <Loader2 className="mr-2 size-4 animate-spin" />
              )}
              Save These Representatives
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
