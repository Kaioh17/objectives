import { describe, expect, it } from "vitest";
import { formatMinutes } from "./format";
import { parseObjectives } from "./store";
import { objectiveInputSchema } from "./types";

const stored = {
  id: "a1",
  title: "Read",
  description: "",
  minutes: 30,
  mode: "daily",
  archived: false,
  createdAt: "2026-10-20T08:00:00.000Z",
  event: null,
};

describe("formatMinutes", () => {
  it("formats minutes and hours", () => {
    expect(formatMinutes(30)).toBe("30 min");
    expect(formatMinutes(60)).toBe("1 h");
    expect(formatMinutes(90)).toBe("1 h 30 min");
  });
});

describe("parseObjectives", () => {
  it("reads valid data and survives junk", () => {
    expect(parseObjectives(JSON.stringify([stored]))).toHaveLength(1);
    expect(parseObjectives(null)).toEqual([]);
    expect(parseObjectives("{not json")).toEqual([]);
    expect(parseObjectives(JSON.stringify([{ ...stored, mode: "yearly" }]))).toEqual([]);
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
