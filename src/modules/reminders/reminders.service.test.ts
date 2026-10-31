import { describe, expect, it } from "vitest";

import { UserError } from "#core/errors.ts";
import { useTestDb } from "#test/helpers/db.ts";

import { cancelReminder, remindersOf, setReminder } from "./reminders.service.ts";

const now = new Date("2026-10-31T12:00:00Z");
const later = (ms: number) => new Date(now.getTime() + ms);
const remind = (userId: string, runAt: Date, reason = "Stretch") =>
  setReminder({ userId, channelId: "100", reason, runAt }, now);

describe("reminders", () => {
  useTestDb();

  it("lists a user's reminders, soonest first", () => {
    const second = remind("1", later(7_200_000), "Second");
    const first = remind("1", later(60_000), "First");
    remind("2", later(30_000), "Someone else's");
    expect(remindersOf("1")).toEqual([
      { id: first.id, runAt: later(60_000), reason: "First" },
      { id: second.id, runAt: later(7_200_000), reason: "Second" },
    ]);
  });

  it("rejects times in the past, more than a year ahead, or invalid", () => {
    expect(() => remind("1", now)).toThrow(UserError);
    expect(() => remind("1", later(366 * 86_400_000))).toThrow(UserError);
    expect(() => remind("1", new Date(Number.NaN))).toThrow(UserError);
    expect(remindersOf("1")).toEqual([]);
  });

  it("cancels only the user's own reminders", () => {
    const { id } = remind("1", later(60_000));
    expect(cancelReminder("2", id)).toBe(false);
    expect(cancelReminder("1", id)).toBe(true);
    expect(cancelReminder("1", id)).toBe(false);
    expect(remindersOf("1")).toEqual([]);
  });
});
