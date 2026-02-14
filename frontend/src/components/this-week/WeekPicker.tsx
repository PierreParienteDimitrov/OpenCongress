"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { CalendarIcon } from "lucide-react";
import { formatDateParam, getWeekStart } from "@/lib/utils";
import { routes } from "@/lib/routes";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

interface WeekPickerProps {
  currentWeekDate: string; // YYYY-MM-DD
  minDate: string; // YYYY-MM-DD
  maxDate: string; // YYYY-MM-DD
}

export default function WeekPicker({
  currentWeekDate,
  minDate,
  maxDate,
}: WeekPickerProps) {
  const router = useRouter();
  const [open, setOpen] = useState(false);

  // Parse YYYY-MM-DD strings as local dates (noon to avoid timezone drift)
  const toLocal = (s: string) => new Date(s + "T12:00:00");
  const selected = toLocal(currentWeekDate);
  const fromDate = toLocal(minDate);
  const toDate = toLocal(maxDate);

  function handleSelect(date: Date | undefined) {
    if (!date) return;
    setOpen(false);
    const weekStart = getWeekStart(date);
    router.push(routes.thisWeek.week(formatDateParam(weekStart)));
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="cursor-pointer gap-2 text-sm"
        >
          <CalendarIcon className="size-4" />
          Pick Week
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="end">
        <Calendar
          mode="single"
          selected={selected}
          onSelect={handleSelect}
          defaultMonth={selected}
          disabled={{ before: fromDate, after: toDate }}
        />
      </PopoverContent>
    </Popover>
  );
}
