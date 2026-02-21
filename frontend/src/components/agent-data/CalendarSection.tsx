"use client";

import { CalendarEvent } from "@/lib/types";

interface CalendarSectionProps {
  calendar: CalendarEvent[];
}

export function CalendarSection({ calendar }: CalendarSectionProps) {
  return (
    <div className="space-y-2">
      {calendar.length === 0 && (
        <p className="text-muted-foreground text-xs italic">No events</p>
      )}
      {calendar.map((evt, i) => (
        <div key={i} className="rounded-md border p-2">
          <p className="text-sm font-medium">{evt.event}</p>
          <p className="text-muted-foreground text-xs">
            {evt.time} &middot; {evt.duration}
          </p>
        </div>
      ))}
    </div>
  );
}
