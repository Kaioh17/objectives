import { z } from "zod";
import { calendarEventSchema } from "@/features/calendar/mock-calendar";

export const MODES = ["daily", "weekly", "monthly"] as const;
export type Mode = (typeof MODES)[number];

export const MODE_LABEL: Record<Mode, string> = {
  daily: "Daily",
  weekly: "Weekly",
  monthly: "Monthly",
};

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
