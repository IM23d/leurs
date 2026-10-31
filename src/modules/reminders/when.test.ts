import { describe, expect, it } from "vitest";

import { parseWhen } from "./when.ts";

// Saturday 31 October 2026, 14:30 UTC, which is 15:30 in Zurich.
const now = new Date("2026-10-31T14:30:00Z");
const at = (text: string, zone = "UTC") => parseWhen(text, now, zone)?.toISOString();

describe("parseWhen", () => {
  it.each([
    ["15m", "2026-10-31T14:45:00.000Z"],
    ["30s", "2026-10-31T14:30:30.000Z"],
    ["2h", "2026-10-31T16:30:00.000Z"],
    ["3d", "2026-11-03T14:30:00.000Z"],
    ["1h30m", "2026-10-31T16:00:00.000Z"],
    ["tomorrow", "2026-11-01T14:30:00.000Z"],
    ["TM", "2026-11-01T14:30:00.000Z"],
  ])("reads the duration %s", (text, expected) => {
    expect(at(text)).toBe(expected);
  });

  it.each([
    ["20:00", "2026-10-31T20:00:00.000Z"],
    ["8pm", "2026-10-31T20:00:00.000Z"],
    ["8:15 pm", "2026-10-31T20:15:00.000Z"],
    ["9am", "2026-11-01T09:00:00.000Z"],
    ["12am", "2026-11-01T00:00:00.000Z"],
    ["12pm", "2026-11-01T12:00:00.000Z"],
    ["14:30", "2026-11-01T14:30:00.000Z"],
  ])("reads the clock time %s as the next time it comes", (text, expected) => {
    expect(at(text)).toBe(expected);
  });

  it("reads clock times in the user's zone", () => {
    expect(at("20:00", "Europe/Zurich")).toBe("2026-10-31T19:00:00.000Z");
    expect(at("15:00", "Europe/Zurich")).toBe("2026-11-01T14:00:00.000Z");
  });

  it.each([
    ["15.12", "2026-12-15T00:00:00.000Z"],
    ["15.05", "2027-05-15T00:00:00.000Z"],
    ["31.10", "2027-10-31T00:00:00.000Z"],
    ["15.05.27", "2027-05-15T00:00:00.000Z"],
    ["15.05.2027", "2027-05-15T00:00:00.000Z"],
    ["15.05.26", "2026-05-15T00:00:00.000Z"],
  ])("reads the date %s", (text, expected) => {
    expect(at(text)).toBe(expected);
  });

  it.each([
    ["15.11:15:25", "2026-11-15T15:25:00.000Z"],
    ["15.07:15:25:30", "2027-07-15T15:25:30.000Z"],
  ])("reads the date and time %s", (text, expected) => {
    expect(at(text)).toBe(expected);
  });

  it("checks 29.02 against the year it lands in", () => {
    const on = (date: string, text: string) =>
      parseWhen(text, new Date(date), "UTC")?.toISOString();
    expect(on("2027-03-10T12:00:00Z", "29.02")).toBe("2028-02-29T00:00:00.000Z");
    expect(on("2027-03-10T12:00:00Z", "29.02:08:30")).toBe("2028-02-29T08:30:00.000Z");
    expect(on("2028-02-01T12:00:00Z", "29.02")).toBe("2028-02-29T00:00:00.000Z");
    expect(on("2028-03-10T12:00:00Z", "29.02")).toBeUndefined();
    expect(on("2028-03-10T12:00:00Z", "29.02:08:30")).toBeUndefined();
  });

  it.each(["", "soon", "25:00", "13pm", "0am", "10:75", "31.02", "15.13", "30.02:10:00", "0m"])(
    "rejects %j",
    (text) => {
      expect(at(text)).toBeUndefined();
    },
  );
});
