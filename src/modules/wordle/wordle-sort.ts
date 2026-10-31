import type { PlayerStats } from "./wordle-stats.ts";

/** Players with no solved game sort after everyone else by average. */
const averageOf = (player: PlayerStats) => player.average ?? Number.POSITIVE_INFINITY;

const byAverage = (a: PlayerStats, b: PlayerStats) => averageOf(a) - averageOf(b);

export const SORTS = {
  crowns: { label: "Crowns", compare: (a, b) => b.crowns - a.crowns || byAverage(a, b) },
  average: { label: "Average", compare: (a, b) => byAverage(a, b) || b.solved - a.solved },
  solved: { label: "Solved", compare: (a, b) => b.solved - a.solved || byAverage(a, b) },
} as const satisfies Record<
  string,
  { label: string; compare: (a: PlayerStats, b: PlayerStats) => number }
>;

export type SortName = keyof typeof SORTS;

export const isSortName = (name: string): name is SortName => name in SORTS;

export const rank = (players: readonly PlayerStats[], sort: SortName): PlayerStats[] =>
  players.toSorted(SORTS[sort].compare);
