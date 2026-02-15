"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { useQuery } from "@tanstack/react-query";
import {
  Users,
  ScrollText,
  Vote,
  CalendarDays,
  Newspaper,
} from "lucide-react";
import { Command as CommandPrimitive } from "cmdk";

import { Badge } from "@/components/ui/badge";
import { searchMembers, searchBills, searchVotes } from "@/lib/api";
import { routes, getMemberRoute } from "@/lib/routes";
import {
  cn,
  getPartyBgColor,
  getResultBgColor,
  getChamberShortName,
  getMemberLocation,
  formatDate,
  truncate,
} from "@/lib/utils";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  // Debounce search input (300ms)
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(timer);
  }, [search]);

  // Cmd+K / Ctrl+K keyboard shortcut
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        onOpenChange(!open);
      }
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, onOpenChange]);

  function handleOpenChange(value: boolean) {
    if (!value) setSearch("");
    onOpenChange(value);
  }

  const searchEnabled = debouncedSearch.length >= 2;

  const { data: membersData, isLoading: membersLoading } = useQuery({
    queryKey: ["search", "members", debouncedSearch],
    queryFn: () => searchMembers(debouncedSearch),
    enabled: searchEnabled,
    staleTime: 30_000,
  });

  const { data: billsData, isLoading: billsLoading } = useQuery({
    queryKey: ["search", "bills", debouncedSearch],
    queryFn: () => searchBills(debouncedSearch),
    enabled: searchEnabled,
    staleTime: 30_000,
  });

  const { data: votesData, isLoading: votesLoading } = useQuery({
    queryKey: ["search", "votes", debouncedSearch],
    queryFn: () => searchVotes(debouncedSearch),
    enabled: searchEnabled,
    staleTime: 30_000,
  });

  const members = membersData?.results ?? [];
  const bills = billsData?.results ?? [];
  const votes = votesData?.results ?? [];
  const isLoading =
    searchEnabled && (membersLoading || billsLoading || votesLoading);
  const hasResults =
    members.length > 0 || bills.length > 0 || votes.length > 0;

  function handleSelect(url: string) {
    handleOpenChange(false);
    router.push(url);
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogHeader className="sr-only">
        <DialogTitle>Search</DialogTitle>
        <DialogDescription>
          Search for members, bills, and votes
        </DialogDescription>
      </DialogHeader>
      <DialogContent
        className="overflow-hidden p-0 top-[20%] translate-y-0 sm:max-w-2xl"
        showCloseButton={false}
      >
        <CommandPrimitive shouldFilter={false}>
          {/* Search input row */}
          <div className="flex items-center gap-3 border-b px-4">
            <svg
              className="size-5 shrink-0 text-muted-foreground"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.3-4.3" />
            </svg>
            <CommandPrimitive.Input
              value={search}
              onValueChange={setSearch}
              placeholder="Search members, bills, votes..."
              className="flex-1 h-14 bg-transparent text-base outline-hidden placeholder:text-muted-foreground"
            />
            <kbd className="pointer-events-none inline-flex items-center rounded border border-border bg-muted px-2 py-0.5 text-xs font-mono text-muted-foreground">
              esc
            </kbd>
          </div>

          {/* Results */}
          <CommandPrimitive.List className="max-h-[min(400px,50vh)] scroll-py-2 overflow-y-auto overflow-x-hidden p-2">
            {isLoading && (
              <div className="py-14 text-center text-sm text-muted-foreground">
                Searching...
              </div>
            )}

            {searchEnabled && !isLoading && !hasResults && (
              <div className="py-14 text-center text-sm text-muted-foreground">
                No results found.
              </div>
            )}

            {/* Quick links (shown when not searching) */}
            {!searchEnabled && !isLoading && (
              <CommandPrimitive.Group
                heading="Pages"
                className="[&_[cmdk-group-heading]]:text-muted-foreground [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5"
              >
                <CommandPrimitive.Item
                  onSelect={() => handleSelect(routes.senate.index)}
                  className="flex items-center gap-2 rounded-sm px-2 py-2 text-sm cursor-pointer select-none data-[selected=true]:bg-accent data-[selected=true]:text-accent-foreground outline-hidden"
                >
                  <Users className="size-4 text-muted-foreground" />
                  Senate
                </CommandPrimitive.Item>
                <CommandPrimitive.Item
                  onSelect={() => handleSelect(routes.house.index)}
                  className="flex items-center gap-2 rounded-sm px-2 py-2 text-sm cursor-pointer select-none data-[selected=true]:bg-accent data-[selected=true]:text-accent-foreground outline-hidden"
                >
                  <Users className="size-4 text-muted-foreground" />
                  House
                </CommandPrimitive.Item>
                <CommandPrimitive.Item
                  onSelect={() => handleSelect(routes.calendar.index)}
                  className="flex items-center gap-2 rounded-sm px-2 py-2 text-sm cursor-pointer select-none data-[selected=true]:bg-accent data-[selected=true]:text-accent-foreground outline-hidden"
                >
                  <CalendarDays className="size-4 text-muted-foreground" />
                  Calendar
                </CommandPrimitive.Item>
                <CommandPrimitive.Item
                  onSelect={() => handleSelect(routes.thisWeek.index)}
                  className="flex items-center gap-2 rounded-sm px-2 py-2 text-sm cursor-pointer select-none data-[selected=true]:bg-accent data-[selected=true]:text-accent-foreground outline-hidden"
                >
                  <Newspaper className="size-4 text-muted-foreground" />
                  This Week
                </CommandPrimitive.Item>
              </CommandPrimitive.Group>
            )}

            {/* Members */}
            {members.length > 0 && (
              <CommandPrimitive.Group
                heading="Members"
                className="[&_[cmdk-group-heading]]:text-muted-foreground [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5"
              >
                {members.map((member) => (
                  <CommandPrimitive.Item
                    key={member.bioguide_id}
                    value={`member-${member.bioguide_id}`}
                    onSelect={() =>
                      handleSelect(
                        getMemberRoute(
                          member.bioguide_id,
                          member.chamber,
                          member.full_name
                        )
                      )
                    }
                    className="flex items-center gap-2 rounded-sm px-2 py-2 text-sm cursor-pointer select-none data-[selected=true]:bg-accent data-[selected=true]:text-accent-foreground outline-hidden"
                  >
                    <Image
                      src={member.photo_url}
                      alt={member.full_name}
                      width={24}
                      height={24}
                      className="rounded-full object-cover"
                    />
                    <span className="font-medium">{member.full_name}</span>
                    <Badge
                      className={cn(
                        "text-[10px] px-1.5 py-0",
                        getPartyBgColor(member.party)
                      )}
                    >
                      {member.party}
                    </Badge>
                    <span className="text-muted-foreground text-xs ml-auto">
                      {getMemberLocation(
                        member.state,
                        member.district,
                        member.chamber
                      )}
                    </span>
                  </CommandPrimitive.Item>
                ))}
              </CommandPrimitive.Group>
            )}

            {/* Bills */}
            {bills.length > 0 && (
              <CommandPrimitive.Group
                heading="Bills"
                className="[&_[cmdk-group-heading]]:text-muted-foreground [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5"
              >
                {bills.map((bill) => (
                  <CommandPrimitive.Item
                    key={bill.bill_id}
                    value={`bill-${bill.bill_id}`}
                    onSelect={() =>
                      handleSelect(routes.legislation.detail(bill.bill_id))
                    }
                    className="flex items-center gap-2 rounded-sm px-2 py-2 text-sm cursor-pointer select-none data-[selected=true]:bg-accent data-[selected=true]:text-accent-foreground outline-hidden"
                  >
                    <ScrollText className="size-4 shrink-0 text-muted-foreground" />
                    <span className="font-medium">{bill.display_number}</span>
                    <span className="text-muted-foreground text-xs truncate">
                      {truncate(bill.short_title || bill.title, 60)}
                    </span>
                    {bill.latest_action_date && (
                      <span className="text-muted-foreground text-xs ml-auto shrink-0">
                        {formatDate(bill.latest_action_date)}
                      </span>
                    )}
                  </CommandPrimitive.Item>
                ))}
              </CommandPrimitive.Group>
            )}

            {/* Votes */}
            {votes.length > 0 && (
              <CommandPrimitive.Group
                heading="Votes"
                className="[&_[cmdk-group-heading]]:text-muted-foreground [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5"
              >
                {votes.map((vote) => (
                  <CommandPrimitive.Item
                    key={vote.vote_id}
                    value={`vote-${vote.vote_id}`}
                    onSelect={() =>
                      handleSelect(routes.vote.detail(vote.vote_id))
                    }
                    className="flex items-center gap-2 rounded-sm px-2 py-2 text-sm cursor-pointer select-none data-[selected=true]:bg-accent data-[selected=true]:text-accent-foreground outline-hidden"
                  >
                    <Vote className="size-4 shrink-0 text-muted-foreground" />
                    <span className="truncate">
                      {truncate(vote.question, 50)}
                    </span>
                    <Badge
                      variant="outline"
                      className="text-[10px] px-1.5 py-0 shrink-0"
                    >
                      {getChamberShortName(vote.chamber)}
                    </Badge>
                    <Badge
                      className={cn(
                        "text-[10px] px-1.5 py-0 shrink-0",
                        getResultBgColor(vote.result)
                      )}
                    >
                      {vote.result}
                    </Badge>
                    <span className="text-muted-foreground text-xs ml-auto shrink-0">
                      {formatDate(vote.date)}
                    </span>
                  </CommandPrimitive.Item>
                ))}
              </CommandPrimitive.Group>
            )}
          </CommandPrimitive.List>
        </CommandPrimitive>
      </DialogContent>
    </Dialog>
  );
}
