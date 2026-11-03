import { eq } from "drizzle-orm";

import { db } from "#db/client.ts";

import type { DailySummary } from "./wordle-parse.ts";
import { computeStats, type PlayerStats } from "./wordle-stats.ts";
import { wordleResults } from "./wordle.schema.ts";

export type { PlayerStats } from "./wordle-stats.ts";

/** Stores a daily summary. Results already stored are kept, so imports can run again. */
export function saveSummary(guildId: string, { puzzleDate, results }: DailySummary): number {
  return results.length === 0
    ? 0
    : db()
        .insert(wordleResults)
        .values(results.map((result) => ({ guildId, puzzleDate, ...result })))
        .onConflictDoNothing()
        .run().changes;
}

export interface GroupStats {
  readonly days: number;
  readonly games: number;
  readonly solved: number;
  readonly players: readonly PlayerStats[];
}

export function groupStats(guildId: string): GroupStats {
  const results = db().select().from(wordleResults).where(eq(wordleResults.guildId, guildId)).all();
  const players = computeStats(results);
  return {
    days: new Set(results.map((result) => result.puzzleDate)).size,
    games: results.length,
    solved: results.filter((result) => result.guesses !== null).length,
    players,
  };
}
