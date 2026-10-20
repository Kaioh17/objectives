import { useEffect, useState } from "react";
import { z } from "zod";
import { apiFetch } from "@/lib/api-client";

const scheduleItemSchema = z.object({
  id: z.string(),
  title: z.string(),
  start: z.string(),
  end: z.string(),
});
export type ScheduleItem = z.infer<typeof scheduleItemSchema>;

const calendarStatusSchema = z.object({ connected: z.boolean(), email: z.string().nullable() });
export type CalendarStatus = z.infer<typeof calendarStatusSchema>;

// date is a local "YYYY-MM-DD". A 409 ApiError means Google Calendar is not connected.
export async function listCalendarEvents(date: string): Promise<ScheduleItem[]> {
  const body = await apiFetch(`/calendar/events?date=${encodeURIComponent(date)}`);
  return z.array(scheduleItemSchema).parse(body);
}

// null while loading or if the status could not be read
export function useCalendarStatus(enabled: boolean): CalendarStatus | null {
  const [status, setStatus] = useState<CalendarStatus | null>(null);
  useEffect(() => {
    if (!enabled) return;
    let stale = false;
    apiFetch("/calendar/status")
      .then((body) => !stale && setStatus(calendarStatusSchema.parse(body)))
      .catch(() => {});
    return () => {
      stale = true;
    };
  }, [enabled]);
  return status;
}
