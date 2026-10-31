import { UserError } from "#core/errors.ts";

/** A day without a time. `month` runs from 1 to 12. */
export interface CalendarDate {
  readonly year: number;
  readonly month: number;
  readonly day: number;
}

const FORMAT = /^(\d{1,2})[-.](\d{1,2})[-.](\d{4})$/;
const MIN_YEAR = 1900;
export const FORMAT_HINT = "Use DD-MM-YYYY or DD.MM.YYYY, e.g. 31-12-2000.";

const isLeapYear = (year: number): boolean =>
  (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0;

const compare = (a: CalendarDate, b: CalendarDate): number =>
  a.year - b.year || a.month - b.month || a.day - b.day;

function isRealDate({ year, month, day }: CalendarDate): boolean {
  const date = new Date(Date.UTC(year, month - 1, day));
  return date.getUTCMonth() === month - 1 && date.getUTCDate() === day;
}

/** Reads "31-12-2000" or "31.12.2000". Throws a UserError for anything that is not a birthday. */
export function parseBirthday(text: string, today: CalendarDate): CalendarDate {
  const match = FORMAT.exec(text.trim());
  const date = match && { year: Number(match[3]), month: Number(match[2]), day: Number(match[1]) };
  if (!date || !isRealDate(date)) throw new UserError(`That isn't a date. ${FORMAT_HINT}`);
  if (compare(date, today) > 0) throw new UserError("Your birthday can't be in the future.");
  if (date.year < MIN_YEAR) throw new UserError(`Enter a year from ${MIN_YEAR} on.`);
  return date;
}

/** The birthday in `year`. A 29 February birthday falls on the 28th in other years. */
function inYear(birthday: CalendarDate, year: number): CalendarDate {
  const leapDayMoved = birthday.month === 2 && birthday.day === 29 && !isLeapYear(year);
  return { year, month: birthday.month, day: leapDayMoved ? 28 : birthday.day };
}

export interface NextBirthday {
  readonly date: CalendarDate;
  /** The age the person turns on that day. */
  readonly age: number;
}

/** The next birthday on or after `today`. */
export function nextBirthday(birthday: CalendarDate, today: CalendarDate): NextBirthday {
  const thisYear = inYear(birthday, today.year);
  const date = compare(thisYear, today) >= 0 ? thisYear : inYear(birthday, today.year + 1);
  return { date, age: date.year - birthday.year };
}

/** "December 31". */
export const formatDay = ({ month, day }: CalendarDate): string =>
  new Intl.DateTimeFormat("en-US", { month: "long", day: "numeric", timeZone: "UTC" }).format(
    Date.UTC(2000, month - 1, day),
  );
