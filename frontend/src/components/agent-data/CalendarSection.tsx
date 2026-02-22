"use client";

import { CalendarEvent } from "@/lib/types";

interface CalendarSectionProps {
  calendar: CalendarEvent[];
}

export function CalendarSection({ calendar }: CalendarSectionProps) {
  return (
    <div className="space-y-2.5">
      {calendar.length === 0 && (
        <p className="text-xs italic text-slate-500 dark:text-slate-400">No events</p>
      )}
      {calendar.map((evt, i) => (
        <div key={i} className="rounded-xl border border-slate-200 bg-slate-50/70 p-3 dark:border-slate-700 dark:bg-slate-800/50">
          <p className="text-sm font-medium text-slate-900 dark:text-slate-100">{evt.event}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {evt.time} &middot; {evt.duration}
          </p>
        </div>
      ))}
    </div>
  );
}
