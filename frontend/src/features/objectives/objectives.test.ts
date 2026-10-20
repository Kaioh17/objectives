import { describe, expect, it } from "vitest";
import { formatMinutes } from "./format";
import { apiObjectiveSchema, objectiveInputSchema } from "./types";

const fromApi = {
  id: 7,
  title: "Read",
  description: "",
  minutes: 30,
  mode: "daily",
  archived: false,
  created_at: "2026-10-20T08:00:00Z",
  event_id: null,
  event_start: null,
  event_end: null,
};

describe("formatMinutes", () => {
  it("formats minutes and hours", () => {
    expect(formatMinutes(30)).toBe("30 min");
    expect(formatMinutes(60)).toBe("1 h");
    expect(formatMinutes(90)).toBe("1 h 30 min");
  });
});

describe("apiObjectiveSchema", () => {
  it("maps the API shape to the UI shape", () => {
    expect(apiObjectiveSchema.parse(fromApi)).toEqual({
      id: "7",
      title: "Read",
      description: "",
      minutes: 30,
      mode: "daily",
      archived: false,
      createdAt: "2026-10-20T08:00:00Z",
      event: null,
    });
  });

  it("folds the event_* triple into one event", () => {
    const scheduled = {
      ...fromApi,
      event_id: "ev1",
      event_start: "2026-11-02T09:00:00Z",
      event_end: "2026-11-02T09:30:00Z",
    };
    expect(apiObjectiveSchema.parse(scheduled).event).toEqual({
      id: "ev1",
      start: "2026-11-02T09:00:00Z",
      end: "2026-11-02T09:30:00Z",
    });
  });

  it("rejects a response it does not understand", () => {
    expect(apiObjectiveSchema.safeParse({ ...fromApi, mode: "yearly" }).success).toBe(false);
  });
});

describe("objectiveInputSchema", () => {
  const valid = { title: "  Read  ", description: "", minutes: 30, mode: "weekly" };

  it("trims and accepts a valid objective", () => {
    expect(objectiveInputSchema.parse(valid).title).toBe("Read");
  });

  it("rejects an empty title and out-of-range minutes", () => {
    expect(objectiveInputSchema.safeParse({ ...valid, title: "  " }).success).toBe(false);
    expect(objectiveInputSchema.safeParse({ ...valid, minutes: 4 }).success).toBe(false);
    expect(objectiveInputSchema.safeParse({ ...valid, minutes: 1441 }).success).toBe(false);
  });
});
