import { describe, expect, it } from "vitest";

import { formatDuration, formatShortDuration, isPermanent, parseDuration } from "./duration.ts";

describe("parseDuration", () => {
  it.each([
    ["30s", 30_000],
    ["5m", 300_000],
    ["1h30m", 5_400_000],
    ["2d 4h", 187_200_000],
    ["1w", 604_800_000],
    ["30sec", 30_000],
    ["30min", 1_800_000],
    ["2 hours", 7_200_000],
    ["1mon", 2_592_000_000],
    ["1 month 2 days", 2_764_800_000],
  ])("reads %s", (input, expected) => {
    expect(parseDuration(input)).toBe(expected);
  });

  it.each(["", "abc", "5", "5x", "0m", "5m extra", "3 apples", "99999y"])("rejects %j", (input) => {
    expect(parseDuration(input)).toBeUndefined();
  });
});

describe("formatDuration", () => {
  it("names each non-zero part", () => {
    expect(formatDuration(90_061_000)).toBe("1 day, 1 hour, 1 minute, 1 second");
    expect(formatDuration(500)).toBe("less than a second");
  });
});

it("recognises permanent", () => {
  expect(isPermanent("Perm")).toBe(true);
  expect(isPermanent("1d")).toBe(false);
});

it("formats short durations for lists", () => {
  expect(formatShortDuration(40_000)).toBe("40s");
  expect(formatShortDuration(300_000)).toBe("5m");
  expect(formatShortDuration(7_500_000)).toBe("2h 5m");
});
