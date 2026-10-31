const UNITS = { s: 1000, m: 60_000, h: 3_600_000, d: 86_400_000, w: 604_800_000 } as const;
const UNIT_NAMES = { s: "second", m: "minute", h: "hour", d: "day", w: "week" } as const;
type Unit = keyof typeof UNITS;

const PART = /(\d+)\s*([smhdw])/gi;

/** Parses "30m", "1h30m" or "2d 4h" into milliseconds. Returns undefined for anything else. */
export function parseDuration(input: string): number | undefined {
  const text = input.trim().toLowerCase();
  if (!/^(\d+\s*[smhdw]\s*)+$/.test(text)) return undefined;
  const total = [...text.matchAll(PART)]
    .map(([, amount, unit]) => Number(amount) * UNITS[unit as Unit])
    .reduce((sum, ms) => sum + ms, 0);
  return total > 0 ? total : undefined;
}

export function isPermanent(input: string): boolean {
  return ["perm", "permanent", "forever"].includes(input.trim().toLowerCase());
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
