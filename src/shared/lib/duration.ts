const UNITS = { s: 1000, m: 60_000, h: 3_600_000, d: 86_400_000, w: 604_800_000 } as const;
const UNIT_NAMES = { s: "second", m: "minute", h: "hour", d: "day", w: "week" } as const;
type Unit = keyof typeof UNITS;

const PART = /(\d+)\s*([smhdw])/gi;
/** Longer durations are almost certainly typos and do not fit in a Date. */
const MAX_DURATION_MS = 10 * 365 * UNITS.d;

/** Parses "30m", "1h30m" or "2d 4h" into milliseconds. Returns undefined for anything else. */
export function parseDuration(input: string): number | undefined {
  const text = input.trim().toLowerCase();
  if (!/^(\d+\s*[smhdw]\s*)+$/.test(text)) return undefined;
  const total = [...text.matchAll(PART)]
    .map(([, amount, unit]) => Number(amount) * UNITS[unit as Unit])
    .reduce((sum, ms) => sum + ms, 0);
  return total > 0 && total <= MAX_DURATION_MS ? total : undefined;
}

export function isPermanent(input: string): boolean {
  return ["perm", "permanent", "forever", "none"].includes(input.trim().toLowerCase());
}

/** Formats milliseconds as "2 days, 3 hours". Drops parts that are zero. */
export function formatDuration(ms: number): string {
  const parts = (Object.keys(UNITS) as Unit[])
    .filter((unit) => unit !== "w")
    .reverse()
    .reduce<{ rest: number; parts: string[] }>(
      ({ rest, parts }, unit) => {
        const amount = Math.floor(rest / UNITS[unit]);
        const name = UNIT_NAMES[unit];
        return {
          rest: rest - amount * UNITS[unit],
          parts: amount > 0 ? [...parts, `${amount} ${name}${amount === 1 ? "" : "s"}`] : parts,
        };
      },
      { rest: ms, parts: [] },
    ).parts;
  return parts.length > 0 ? parts.join(", ") : "less than a second";
}

/** Formats milliseconds compactly for lists: "2h 5m", "5m", "40s". */
export function formatShortDuration(ms: number): string {
  const totalMinutes = Math.floor(ms / UNITS.m);
  if (totalMinutes === 0) return `${Math.max(0, Math.floor(ms / UNITS.s))}s`;
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return hours === 0 ? `${minutes}m` : `${hours}h ${minutes}m`;
}
