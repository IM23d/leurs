import { fromWallClock, wallClock, type WallClock } from "#modules/timezones/api.ts";
import { parseDuration } from "#shared/lib/duration.ts";

const DAY_MS = 86_400_000;

const CLOCK = /^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$/;
const DATE = /^(\d{1,2})\.(\d{1,2})(?:\.(\d{2}|\d{4}))?$/;
const DATE_TIME = /^(\d{1,2})\.(\d{1,2}):(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?$/;

const isRealDate = (year: number, month: number, day: number): boolean => {
  const date = new Date(Date.UTC(year, month - 1, day));
  return date.getUTCMonth() === month - 1 && date.getUTCDate() === day;
};

const isRealTime = (hour: number, minute: number, second: number): boolean =>
  hour <= 23 && minute <= 59 && second <= 59;

function to24Hour(hour: number, meridiem: string | undefined): number | undefined {
  if (meridiem === undefined) return hour;
  if (hour < 1 || hour > 12) return undefined;
  return (hour % 12) + (meridiem === "pm" ? 12 : 0);
}

/** "20:00" or "8pm": the next time the clock shows it, today or tomorrow. */
function clockTime(text: string, now: Date, zone: string): Date | undefined {
  const match = CLOCK.exec(text);
  if (!match) return undefined;
  const hour = to24Hour(Number(match[1]), match[3]);
  const minute = Number(match[2] ?? 0);
  if (hour === undefined || !isRealTime(hour, minute, 0)) return undefined;
  const today = { ...wallClock(now, zone), hour, minute, second: 0 };
  const target = fromWallClock(today, zone);
  return target > now ? target : fromWallClock({ ...today, day: today.day + 1 }, zone);
}

/** The wall clock in this year, or next year when it has already passed. */
function nextOccurrence(wall: WallClock, now: Date, zone: string): Date {
  const target = fromWallClock(wall, zone);
  return target > now ? target : fromWallClock({ ...wall, year: wall.year + 1 }, zone);
}

/** "15.05", "15.05.26" or "15.05.2026": midnight on that day. */
function calendarDate(text: string, now: Date, zone: string): Date | undefined {
  const match = DATE.exec(text);
  if (!match) return undefined;
  const [day, month] = [Number(match[1]), Number(match[2])];
  const givenYear = match[3] === undefined ? undefined : Number(match[3]);
  const year =
    givenYear === undefined ? wallClock(now, zone).year : givenYear + (givenYear < 100 ? 2000 : 0);
  if (!isRealDate(year, month, day)) return undefined;
  const wall = { year, month, day, hour: 0, minute: 0, second: 0 };
  // A date with an explicit year stays put, so a past date is reported as past.
  return givenYear === undefined ? nextOccurrence(wall, now, zone) : fromWallClock(wall, zone);
}

/** "15.07:15:25" or "15.07:15:25:00": day.month:hour:minute[:second]. */
function dateTime(text: string, now: Date, zone: string): Date | undefined {
  const match = DATE_TIME.exec(text);
  if (!match) return undefined;
  const part = (index: number) => Number(match[index] ?? 0);
  const [day, month, hour, minute, second] = [part(1), part(2), part(3), part(4), part(5)];
  const { year } = wallClock(now, zone);
  const valid = isRealDate(year, month, day) && isRealTime(hour, minute, second);
  return valid ? nextOccurrence({ year, month, day, hour, minute, second }, now, zone) : undefined;
}

/**
 * Reads the old bot's reminder times: a duration such as "15m" or "1h30m", "tomorrow" or "tm",
 * a clock time, a date, or a date with a time. Clock times and dates are read in `zone`.
 */
export function parseWhen(input: string, now: Date, zone: string): Date | undefined {
  const text = input.trim().toLowerCase();
  const offset = parseDuration(text) ?? (text === "tomorrow" || text === "tm" ? DAY_MS : undefined);
  return offset === undefined
    ? (clockTime(text, now, zone) ?? calendarDate(text, now, zone) ?? dateTime(text, now, zone))
    : new Date(now.getTime() + offset);
}

export const WHEN_FORMATS = [
  "`15m` or `1h30m` (also s, h, d and w)",
  "`20:00` or `8pm`",
  "`tomorrow` or `tm`",
  "`15.05` or `15.05.26` (a date)",
  "`15.07:15:25` (day.month:hour:minute)",
];
