import { z } from "zod";

export const calendarEventSchema = z.object({
  id: z.string(),
  start: z.string(),
  end: z.string(),
});
export type CalendarEvent = z.infer<typeof calendarEventSchema>;

// ponytail: mock. Google Calendar lives in the backend; replace the body with an apiFetch call
// (src/lib/api-client.ts) and keep this signature so no caller changes.
export async function createCalendarEvent(input: {
  title: string;
  description: string;
  start: Date;
  minutes: number;
}): Promise<CalendarEvent> {
  await new Promise((resolve) => setTimeout(resolve, 600));
  return {
    id: `mock-${Date.now().toString(36)}`,
    start: input.start.toISOString(),
    end: new Date(input.start.getTime() + input.minutes * 60_000).toISOString(),
  };
}

export type ScheduleItem = { id: string; title: string; start: string; end: string };

type Slot = [title: string, from: string, to: string];

// ponytail: mock weekday template. Replace with GET /calendar/events once Google OAuth exists in the backend.
const STANDUP: Slot = ["Team standup", "09:30", "10:00"];
const LUNCH: Slot = ["Lunch", "12:30", "13:30"];
const WEEKDAY: Record<number, Slot[]> = {
  1: [STANDUP, LUNCH, ["Planning", "14:00", "15:30"]],
  2: [STANDUP, ["1:1 with manager", "11:00", "11:30"], LUNCH],
  3: [STANDUP, LUNCH, ["Design review", "14:00", "15:00"]],
  4: [STANDUP, LUNCH, ["Dentist", "16:00", "17:00"]],
  5: [STANDUP, LUNCH, ["Demo day", "15:00", "16:00"]],
};

// date is a local "YYYY-MM-DD"; weekends are empty
export async function listCalendarEvents(date: string): Promise<ScheduleItem[]> {
  await new Promise((resolve) => setTimeout(resolve, 300));
  const iso = (time: string) => new Date(`${date}T${time}`).toISOString();
  return (WEEKDAY[new Date(`${date}T00:00`).getDay()] ?? []).map(([title, from, to]) => ({
    id: `${date}-${from}`,
    title,
    start: iso(from),
    end: iso(to),
  }));
}
