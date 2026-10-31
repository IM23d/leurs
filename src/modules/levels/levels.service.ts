import { inArray, sql } from "drizzle-orm";

import { db } from "#db/client.ts";

import { BASE_MESSAGE_XP, levelForXp } from "./levels.math.ts";
import { levels } from "./levels.schema.ts";

export interface LevelStats {
  xp: number;
  level: number;
  messages: number;
  voiceSeconds: number;
}

type Counters = Omit<LevelStats, "level">;

const ZERO: Counters = { xp: 0, messages: 0, voiceSeconds: 0 };

/** Gains not yet written to the database, by user ID. Written by flushLevels(). */
const pending = new Map<string, Counters>();

const sum = (a: Counters, b: Counters): Counters => ({
  xp: a.xp + b.xp,
  messages: a.messages + b.messages,
  voiceSeconds: a.voiceSeconds + b.voiceSeconds,
});

const withLevel = (counters: Counters): LevelStats => ({
  ...counters,
  level: levelForXp(counters.xp),
});

export function addPending(userId: string, gain: Partial<Counters>): void {
  pending.set(userId, sum(pending.get(userId) ?? ZERO, { ...ZERO, ...gain }));
}

function storedCounters(userIds: readonly string[]): Map<string, Counters> {
  if (userIds.length === 0) return new Map();
  const rows = db()
    .select()
    .from(levels)
    .where(inArray(levels.userId, [...userIds]))
    .all();
  return new Map(rows.map(({ userId, ...counters }) => [userId, counters]));
}

/** Stored and pending counters of the given users. Users with neither are left out. */
function currentCounters(userIds: readonly string[]): Map<string, Counters> {
  const stored = storedCounters(userIds);
  return new Map(
    [...new Set(userIds)].flatMap((userId) => {
      const saved = stored.get(userId);
      const gain = pending.get(userId);
      return saved || gain ? [[userId, sum(saved ?? ZERO, gain ?? ZERO)] as const] : [];
    }),
  );
}

export const getStats = (userId: string): LevelStats =>
  withLevel(currentCounters([userId]).get(userId) ?? ZERO);

/** Sets a user's message count and the XP that many average messages give, like the old setlevel. */
export function setMessages(userId: string, messages: number): LevelStats {
  const xp = messages * BASE_MESSAGE_XP;
  const gain = pending.get(userId);
  if (gain) pending.set(userId, { ...gain, xp: 0, messages: 0 });
  db()
    .insert(levels)
    .values({ userId, xp, messages })
    .onConflictDoUpdate({ target: levels.userId, set: { xp, messages } })
    .run();
  return getStats(userId);
}

/** Writes every pending gain in one transaction. Returns the number of users written. */
export function flushLevels(): number {
  const gains = [...pending];
  if (gains.length === 0) return 0;
  db().transaction((tx) => {
    for (const [userId, gain] of gains) {
      tx.insert(levels)
        .values({ userId, ...gain })
        .onConflictDoUpdate({
          target: levels.userId,
          set: {
            xp: sql`${levels.xp} + ${gain.xp}`,
            messages: sql`${levels.messages} + ${gain.messages}`,
            voiceSeconds: sql`${levels.voiceSeconds} + ${gain.voiceSeconds}`,
          },
        })
        .run();
    }
  });
  // Cleared only after the commit, so a failed write is retried on the next flush.
  pending.clear();
  return gains.length;
}

/** Best first: most XP, then most messages. */
export const levelRanking = (
  userIds: readonly string[],
): { userId: string; level: number; xp: number; messages: number }[] =>
  [...currentCounters(userIds)]
    .map(([userId, counters]) => ({ userId, ...withLevel(counters) }))
    .filter(({ xp, messages }) => xp > 0 || messages > 0)
    .toSorted((a, b) => b.xp - a.xp || b.messages - a.messages)
    .map(({ userId, level, xp, messages }) => ({ userId, level, xp, messages }));

/** Best first: most seconds in voice. */
export const voiceRanking = (userIds: readonly string[]): { userId: string; seconds: number }[] =>
  [...currentCounters(userIds)]
    .map(([userId, { voiceSeconds }]) => ({ userId, seconds: voiceSeconds }))
    .filter(({ seconds }) => seconds > 0)
    .toSorted((a, b) => b.seconds - a.seconds);

/** Writes rows from the old bot, replacing what is stored. Returns the number of rows. */
export function importStats(rows: readonly ({ userId: string } & Counters)[]): number {
  for (const row of rows) {
    db().insert(levels).values(row).onConflictDoUpdate({ target: levels.userId, set: row }).run();
  }
  return rows.length;
}
