import { z } from "zod";

export const MODES = ["daily", "weekly", "monthly"] as const;
export type Mode = (typeof MODES)[number];

export const MODE_LABEL: Record<Mode, string> = {
  daily: "Daily",
  weekly: "Weekly",
  monthly: "Monthly",
};

// The Google Calendar event an objective was scheduled as
const calendarEventSchema = z.object({ id: z.string(), start: z.string(), end: z.string() });

export const objectiveSchema = z.object({
  id: z.string(),
  title: z
    .string()
    .trim()
    .min(1, "Enter a title.")
    .max(120, "Keep the title under 120 characters."),
  description: z.string().trim().max(500, "Keep the description under 500 characters."),
  minutes: z
    .number("Enter the time in minutes.")
    .int("Use whole minutes.")
    .min(5, "Enter at least 5 minutes.")
    .max(1440, "Enter 1,440 minutes (24 hours) or less."),
  mode: z.enum(MODES),
  archived: z.boolean(),
  createdAt: z.string(),
  event: calendarEventSchema.nullable(),
});
export type Objective = z.infer<typeof objectiveSchema>;

// What the user types in the form
export const objectiveInputSchema = objectiveSchema.pick({
  title: true,
  description: true,
  minutes: true,
  mode: true,
});
export type ObjectiveInput = z.infer<typeof objectiveInputSchema>;

// The API speaks snake_case, integer ids and a flat event_* triple; the UI wants the Objective above
export const apiObjectiveSchema = z
  .object({
    id: z.number(),
    title: z.string(),
    description: z.string(),
    minutes: z.number(),
    mode: z.enum(MODES),
    archived: z.boolean(),
    created_at: z.string(),
    event_id: z.string().nullable(),
    event_start: z.string().nullable(),
    event_end: z.string().nullable(),
  })
  .transform((o): Objective => ({
    id: String(o.id),
    title: o.title,
    description: o.description,
    minutes: o.minutes,
    mode: o.mode,
    archived: o.archived,
    createdAt: o.created_at,
    event:
      o.event_id && o.event_start && o.event_end
        ? { id: o.event_id, start: o.event_start, end: o.event_end }
        : null,
  }));
