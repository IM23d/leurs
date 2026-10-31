import { describe, expect, it } from "vitest";

import { UserError } from "#core/errors.ts";

import { formatDay, nextBirthday, parseBirthday } from "./birthday-dates.ts";

const today = { year: 2026, month: 10, day: 31 };

describe("parseBirthday", () => {
  it.each([
    ["31-12-2000", { year: 2000, month: 12, day: 31 }],
    ["31.12.2000", { year: 2000, month: 12, day: 31 }],
    ["1-2-1990", { year: 1990, month: 2, day: 1 }],
    ["29.02.2004", { year: 2004, month: 2, day: 29 }],
    ["31-10-2026", { year: 2026, month: 10, day: 31 }],
  ])("reads %s", (text, date) => {
    expect(parseBirthday(text, today)).toEqual(date);
  });

  it.each(["2000-12-31", "31/12/2000", "31-12-00", "32-01-2000", "29-02-2001", "nope"])(
    "rejects the format or date %j",
    (text) => {
      expect(() => parseBirthday(text, today)).toThrow("That isn't a date.");
    },
  );

  it("rejects future dates and years before 1900", () => {
    expect(() => parseBirthday("01-11-2026", today)).toThrow(UserError);
    expect(() => parseBirthday("01-01-1899", today)).toThrow("1900");
  });
});

describe("nextBirthday", () => {
  it("is today when the birthday is today", () => {
    expect(nextBirthday({ year: 2000, month: 10, day: 31 }, today)).toEqual({
      date: { year: 2026, month: 10, day: 31 },
      age: 26,
    });
  });

  it("is later this year when it has not passed", () => {
    expect(nextBirthday({ year: 2000, month: 12, day: 24 }, today)).toEqual({
      date: { year: 2026, month: 12, day: 24 },
      age: 26,
    });
  });

  it("is next year when it has passed", () => {
    expect(nextBirthday({ year: 1995, month: 3, day: 1 }, today)).toEqual({
      date: { year: 2027, month: 3, day: 1 },
      age: 32,
    });
  });

  it("moves 29 February to the 28th outside leap years", () => {
    expect(nextBirthday({ year: 2004, month: 2, day: 29 }, today).date).toEqual({
      year: 2027,
      month: 2,
      day: 28,
    });
    expect(
      nextBirthday({ year: 2004, month: 2, day: 29 }, { year: 2027, month: 3, day: 1 }),
    ).toEqual({ date: { year: 2028, month: 2, day: 29 }, age: 24 });
  });
});

describe("formatDay", () => {
  it("names the month", () => {
    expect(formatDay({ year: 2000, month: 12, day: 31 })).toBe("December 31");
    expect(formatDay({ year: 2004, month: 2, day: 29 })).toBe("February 29");
  });
});
