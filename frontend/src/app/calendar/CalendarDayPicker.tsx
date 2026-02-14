"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils";

interface CalendarDayPickerProps {
  weekDates: string[]; // "YYYY-MM-DD" strings
  today: string;
  weekParam: string | null;
}

export function CalendarDayPicker({
  weekDates,
  today,
  weekParam,
}: CalendarDayPickerProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const currentDay = searchParams.get("day");

  // Default active day
  const activeDay =
    currentDay && weekDates.includes(currentDay)
      ? currentDay
      : weekDates.includes(today)
        ? today
        : weekDates[0];

  const handleDayClick = (dateStr: string) => {
    const params = new URLSearchParams();
    if (weekParam) params.set("week", weekParam);
    params.set("day", dateStr);
    router.push(`/calendar?${params.toString()}`, { scroll: false });
  };

  return (
    <div className="flex justify-between gap-1">
      {weekDates.map((dateStr) => {
        const date = new Date(dateStr + "T12:00:00");
        const dayName = date
          .toLocaleDateString("en-US", { weekday: "short" })
          .charAt(0);
        const dayNumber = date.getDate();
        const isToday = dateStr === today;
        const isActive = dateStr === activeDay;

        return (
          <button
            key={dateStr}
            onClick={() => handleDayClick(dateStr)}
            className={cn(
              "cursor-pointer flex-1 flex flex-col items-center py-2 rounded-lg transition-colors",
              isActive
                ? "bg-accent/15"
                : "hover:bg-secondary"
            )}
          >
            <span className="text-[10px] font-medium text-muted-foreground">
              {dayName}
            </span>
            <span
              className={cn(
                "mt-0.5 flex size-8 items-center justify-center rounded-full text-sm font-semibold",
                isToday
                  ? "bg-accent text-white"
                  : isActive
                    ? "text-accent"
                    : "text-foreground"
              )}
            >
              {dayNumber}
            </span>
          </button>
        );
      })}
    </div>
  );
}
