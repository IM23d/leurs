import { eq } from "drizzle-orm";

import { db } from "#db/client.ts";
import { fromWallClock, wallClock, zoneFor } from "#modules/timezones/api.ts";

import { nextBirthday, type CalendarDate, type NextBirthday } from "./birthday-dates.ts";
import { birthdays } from "./birthdays.schema.ts";

export interface Upcoming extends NextBirthday {
  readonly userId: string;
  /** Midnight of the next birthday in the person's own time zone. */
  readonly at: Date;
}

const toDate = ({ year, month, day }: CalendarDate): CalendarDate => ({ year, month, day });

export function getBirthday(userId: string): CalendarDate | undefined {
  const row = db().select().from(birthdays).where(eq(birthdays.userId, userId)).get();
  return row && toDate(row);
}

export function setBirthday(userId: string, date: CalendarDate): void {
  db()
    .insert(birthdays)
    .values({ userId, ...date })
    .onConflictDoUpdate({ target: birthdays.userId, set: date })
    .run();
}

/** "Today" for a user: the date in their time zone, or in UTC. */
export const todayFor = (userId: string, now = new Date()): CalendarDate =>
  toDate(wallClock(now, zoneFor(userId)));

export function upcomingBirthday(
  userId: string,
  birthday: CalendarDate,
  now = new Date(),
): Upcoming {
  const zone = zoneFor(userId);
  const next = nextBirthday(birthday, toDate(wallClock(now, zone)));
  const at = fromWallClock({ ...next.date, hour: 0, minute: 0, second: 0 }, zone);
  return { ...next, userId, at };
}

/** Upcoming birthdays of the given users, soonest first. */
export function upcomingBirthdays(userIds: ReadonlySet<string>, now = new Date()): Upcoming[] {
  return db()
    .select()
    .from(birthdays)
    .all()
    .filter((row) => userIds.has(row.userId))
    .map((row) => upcomingBirthday(row.userId, toDate(row), now))
    .toSorted((a, b) => a.at.getTime() - b.at.getTime());
}

/** IDs of every user with a birthday, so callers can check which are server members. */
export const birthdayUserIds = (): string[] =>
  db()
    .select({ userId: birthdays.userId })
    .from(birthdays)
    .all()
    .map((row) => row.userId);
