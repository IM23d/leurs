import { ABBREVIATION_ZONES, CITY_ZONES } from "./zone-names.ts";

/** A date and time as the clocks in one zone show it. `month` runs from 1 to 12. */
export interface WallClock {
  readonly year: number;
  readonly month: number;
  readonly day: number;
  readonly hour: number;
  readonly minute: number;
  readonly second: number;
}

const MAX_SUGGESTIONS = 25;

const IANA_ZONES = [
  ...new Set([
    ...Intl.supportedValuesOf("timeZone"),
    "UTC",
    ...Object.values(CITY_ZONES),
    ...Object.values(ABBREVIATION_ZONES),
  ]),
].toSorted();

const formatters = new Map<string, Intl.DateTimeFormat>();

function partsFormatter(zone: string): Intl.DateTimeFormat {
  const cached = formatters.get(zone);
  if (cached) return cached;
  const created = new Intl.DateTimeFormat("en-US", {
    timeZone: zone,
    hourCycle: "h23",
    year: "numeric",
    month: "numeric",
    day: "numeric",
    hour: "numeric",
    minute: "numeric",
    second: "numeric",
  });
  formatters.set(zone, created);
  return created;
}

export function wallClock(date: Date, zone: string): WallClock {
  const parts = Object.fromEntries(
    partsFormatter(zone)
      .formatToParts(date)
      .map((part) => [part.type, Number(part.value)]),
  );
  return {
    year: parts["year"] ?? 0,
    month: parts["month"] ?? 1,
    day: parts["day"] ?? 1,
    hour: parts["hour"] ?? 0,
    minute: parts["minute"] ?? 0,
    second: parts["second"] ?? 0,
  };
}

const utcOf = (wall: WallClock): number =>
  Date.UTC(wall.year, wall.month - 1, wall.day, wall.hour, wall.minute, wall.second);

/**
 * The instant at which clocks in `zone` show `wall`. Out-of-range fields roll over, so day 32
 * is the first of the next month.
 */
export function fromWallClock(wall: WallClock, zone: string): Date {
  const target = utcOf(wall);
  const offsetAt = (instant: number) => utcOf(wallClock(new Date(instant), zone)) - instant;
  // The second pass corrects the guess when a DST change lies between the two instants.
  const guess = target - offsetAt(target);
  return new Date(target - offsetAt(guess));
}

export function isValidZone(zone: string): boolean {
  try {
    new Intl.DateTimeFormat("en-US", { timeZone: zone });
    return true;
  } catch {
    return false;
  }
}

const keyOf = (query: string): string => query.trim().toLowerCase().replaceAll(/\s+/g, "_");

function exactZone(query: string): string | undefined {
  const lower = query.trim().toLowerCase();
  return IANA_ZONES.find((zone) => zone.toLowerCase() === lower);
}

/**
 * Finds a time zone from a city, an abbreviation such as CET, or an IANA name. Checks the old
 * bot's shortcuts first so "est" keeps meaning New York, not the fixed EST zone.
 */
export function findTimezone(query: string): string | undefined {
  const key = keyOf(query);
  if (key === "") return undefined;
  return (
    CITY_ZONES[key] ??
    ABBREVIATION_ZONES[key] ??
    exactZone(query) ??
    Object.entries(CITY_ZONES).find(([city]) => city.includes(key))?.[1] ??
    (isValidZone(query.trim()) ? query.trim() : undefined)
  );
}

const cityLabel = (city: string): string =>
  city
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");

/** Autocomplete choices for a partly typed zone. The value is always an IANA name. */
export function suggestZones(query: string): { name: string; value: string }[] {
  const key = keyOf(query);
  const cities = Object.entries(CITY_ZONES)
    .filter(([city]) => city.includes(key))
    .map(([city, zone]) => ({ name: `${cityLabel(city)} (${zone})`, value: zone }));
  const abbreviations = Object.entries(ABBREVIATION_ZONES)
    .filter(([abbreviation]) => key !== "" && abbreviation.startsWith(key))
    .map(([abbreviation, zone]) => ({
      name: `${abbreviation.toUpperCase()} (${zone})`,
      value: zone,
    }));
  const zones = IANA_ZONES.filter((zone) => key !== "" && zone.toLowerCase().includes(key)).map(
    (zone) => ({ name: zone, value: zone }),
  );
  return [...abbreviations, ...cities, ...zones].slice(0, MAX_SUGGESTIONS);
}

/** Formats a time the way the old bot did: "October 31, 05:45 PM" or "October 31, 17:45". */
export function formatClock(date: Date, zone: string, use24Hour: boolean): string {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: zone,
    month: "long",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: use24Hour ? "h23" : "h12",
  }).formatToParts(date);
  const part = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((candidate) => candidate.type === type)?.value ?? "";
  const time = `${part("hour")}:${part("minute")}`;
  return `${part("month")} ${part("day")}, ${use24Hour ? time : `${time} ${part("dayPeriod")}`}`;
}
