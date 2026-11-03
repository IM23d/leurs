import { describe, expect, it } from "vitest";

import { setZone } from "#modules/timezones/timezones.service.ts";
import { useTestDb } from "#test/helpers/db.ts";

import {
  getBirthday,
  setBirthday,
  upcomingBirthday,
  upcomingBirthdays,
} from "./birthdays.service.ts";

const now = new Date("2026-10-31T12:00:00Z");

describe("birthdays", () => {
  useTestDb();

  it("stores one birthday per user", () => {
    expect(getBirthday("1")).toBeUndefined();
    setBirthday("1", { year: 2000, month: 1, day: 2 });
    setBirthday("1", { year: 2001, month: 3, day: 4 });
    expect(getBirthday("1")).toEqual({ year: 2001, month: 3, day: 4 });
  });

  it("puts the next birthday at midnight in the user's zone", () => {
    const birthday = { year: 2000, month: 12, day: 24 };
    expect(upcomingBirthday("1", birthday, now).at).toEqual(new Date("2026-12-24T00:00:00Z"));
    setZone("1", "Europe/Zurich");
    expect(upcomingBirthday("1", birthday, now)).toEqual({
      userId: "1",
      date: { year: 2026, month: 12, day: 24 },
      age: 26,
      at: new Date("2026-12-23T23:00:00Z"),
    });
  });

  it("uses the date in the user's zone as today", () => {
    // 23:30 UTC on 31 October is already 1 November in Tokyo.
    const lateNow = new Date("2026-10-31T23:30:00Z");
    setZone("1", "Asia/Tokyo");
    expect(upcomingBirthday("1", { year: 2000, month: 10, day: 31 }, lateNow).date.year).toBe(2027);
  });

  it("lists the given users soonest first", () => {
    setBirthday("1", { year: 2000, month: 3, day: 1 });
    setBirthday("2", { year: 2000, month: 11, day: 5 });
    setBirthday("3", { year: 2000, month: 12, day: 1 });
    setBirthday("4", { year: 2000, month: 11, day: 1 });
    const ids = upcomingBirthdays(new Set(["1", "2", "3"]), now).map((entry) => entry.userId);
    expect(ids).toEqual(["2", "3", "1"]);
  });
});
