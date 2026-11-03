import type { WordleResult } from "./wordle.schema.ts";

const DAY_MS = 86_400_000;

export interface PlayerStats {
  readonly userId: string;
  readonly played: number;
  readonly solved: number;
  /** Average guesses over solved games. Undefined when nothing was solved. */
  readonly average: number | undefined;
  /** Index 0 to 5 for 1 to 6 guesses, index 6 for unsolved. */
  readonly distribution: readonly number[];
  /** Days with the best score in the group, ties included. */
  readonly crowns: number;
  /** Solved days in a row, ending with the group's latest puzzle. */
  readonly currentStreak: number;
  readonly bestStreak: number;
}

const dayNumber = (date: string) => Math.round(Date.parse(`${date}T00:00:00Z`) / DAY_MS);

/** The longest run of consecutive days, and the run that ends on `lastDay`. */
function streaks(days: readonly number[], lastDay: number): { current: number; best: number } {
  const sorted = [...new Set(days)].toSorted((a, b) => a - b);
  const runs = sorted.reduce<{ day: number; length: number }[]>((all, day) => {
    const previous = all.at(-1);
    return previous?.day === day - 1
      ? [...all.slice(0, -1), { day, length: previous.length + 1 }]
      : [...all, { day, length: 1 }];
  }, []);
  const last = runs.at(-1);
  return {
    best: Math.max(0, ...runs.map((run) => run.length)),
    current: last?.day === lastDay ? last.length : 0,
  };
}

/** Stats for every player in `results`, which should all come from one server. */
export function computeStats(results: readonly WordleResult[]): PlayerStats[] {
  const bestByDay = new Map<string, number>();
  for (const { puzzleDate, guesses } of results) {
    if (guesses !== null) {
      bestByDay.set(puzzleDate, Math.min(guesses, bestByDay.get(puzzleDate) ?? 7));
    }
  }
  const lastDay = Math.max(...results.map((result) => dayNumber(result.puzzleDate)));
  return [...Map.groupBy(results, (result) => result.userId)].map(([userId, games]) => {
    const solved = games.filter((game) => game.guesses !== null);
    const total = solved.reduce((sum, game) => sum + (game.guesses ?? 0), 0);
    const { current, best } = streaks(
      solved.map((game) => dayNumber(game.puzzleDate)),
      lastDay,
    );
    return {
      userId,
      played: games.length,
      solved: solved.length,
      average: solved.length > 0 ? total / solved.length : undefined,
      distribution: [1, 2, 3, 4, 5, 6, null].map(
        (guesses) => games.filter((game) => game.guesses === guesses).length,
      ),
      crowns: solved.filter((game) => bestByDay.get(game.puzzleDate) === game.guesses).length,
      currentStreak: current,
      bestStreak: best,
    };
  });
}
