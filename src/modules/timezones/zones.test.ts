import { describe, expect, it } from "vitest";

import { findTimezone, formatClock, fromWallClock, suggestZones, wallClock } from "./zones.ts";

describe("findTimezone", () => {
  it.each([
    ["Berlin", "Europe/Berlin"],
    ["new york", "America/New_York"],
    ["CEST", "Europe/Paris"],
    ["est", "America/New_York"],
    ["gmt+2", "Etc/GMT-2"],
    ["europe/zurich", "Europe/Zurich"],
    ["Asia/Kolkata", "Asia/Kolkata"],
    ["utc", "UTC"],
    ["franc", "America/Los_Angeles"],
    ["Etc/GMT+5", "Etc/GMT+5"],
  ])("reads %s as %s", (query, zone) => {
    expect(findTimezone(query)).toBe(zone);
  });

  it.each(["", "  ", "atlantis", "Mars/Olympus"])("rejects %j", (query) => {
    expect(findTimezone(query)).toBeUndefined();
  });
});

describe("suggestZones", () => {
  it("offers cities, abbreviations and IANA names", () => {
    const names = suggestZones("ber").map((choice) => choice.name);
    expect(names).toContain("Berlin (Europe/Berlin)");
    expect(names).toContain("Europe/Berlin");
    expect(suggestZones("cet")[0]).toEqual({ name: "CET (Europe/Paris)", value: "Europe/Paris" });
  });

  it("returns at most 25 choices", () => {
    expect(suggestZones("")).toHaveLength(25);
    expect(suggestZones("a").length).toBeLessThanOrEqual(25);
  });

  it("only suggests values that findTimezone accepts", () => {
    for (const { value } of suggestZones("america")) expect(findTimezone(value)).toBe(value);
  });
});

describe("formatClock", () => {
  const date = new Date("2026-10-31T16:05:00Z");

  it("formats 12 and 24 hour time like the old bot", () => {
    expect(formatClock(date, "Europe/Berlin", false)).toBe("October 31, 05:05 PM");
    expect(formatClock(date, "Europe/Berlin", true)).toBe("October 31, 17:05");
  });

  it("shows midnight as 12 AM and 00", () => {
    const midnight = new Date("2026-01-05T00:00:00Z");
    expect(formatClock(midnight, "UTC", false)).toBe("January 05, 12:00 AM");
    expect(formatClock(midnight, "UTC", true)).toBe("January 05, 00:00");
  });
});

describe("wall clocks", () => {
  it("reads the wall clock in a zone", () => {
    expect(wallClock(new Date("2026-07-01T22:30:15Z"), "Europe/Zurich")).toEqual({
      year: 2026,
      month: 7,
      day: 2,
      hour: 0,
      minute: 30,
      second: 15,
    });
  });

  it.each([
    ["2026-07-01T12:00:00Z", "Europe/Zurich"],
    ["2026-01-15T03:45:00Z", "America/New_York"],
    ["2026-03-29T01:30:00Z", "Europe/Berlin"],
    ["2026-04-05T15:00:00Z", "Australia/Sydney"],
  ])("turns the wall clock of %s in %s back into the same instant", (iso, zone) => {
    const instant = new Date(iso);
    expect(fromWallClock(wallClock(instant, zone), zone)).toEqual(instant);
  });

  it("picks a matching instant for an hour that clocks show twice", () => {
    const wall = { year: 2026, month: 10, day: 25, hour: 2, minute: 30, second: 0 };
    expect(wallClock(fromWallClock(wall, "Europe/Berlin"), "Europe/Berlin")).toEqual(wall);
  });

  it("rolls over out-of-range days", () => {
    const wall = { year: 2026, month: 12, day: 32, hour: 9, minute: 0, second: 0 };
    expect(fromWallClock(wall, "UTC")).toEqual(new Date("2027-01-01T09:00:00Z"));
  });
});
