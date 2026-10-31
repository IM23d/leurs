const SUMMARY = /Here are yesterday's results/i;
const RESULT_LINE = /^(?:👑\s*)?([1-6X])\/6:\s*(.+)$/u;
const MENTION = /<@!?(\d{17,20})>/g;
const DAY_MS = 86_400_000;

interface ParsedResult {
  readonly userId: string;
  /** Null for an unsolved game. */
  readonly guesses: number | null;
}

export interface DailySummary {
  readonly puzzleDate: string;
  readonly results: readonly ParsedResult[];
}

/**
 * Reads the Wordle app's daily summary, e.g. "👑 3/6: <@1> <@2>\nX/6: <@3>". Returns undefined
 * for any other message. The summary reports the previous day's puzzle.
 */
export function parseDailySummary(content: string, postedAt: Date): DailySummary | undefined {
  if (!SUMMARY.test(content)) return undefined;
  const results = content.split("\n").flatMap((line) => {
    const match = RESULT_LINE.exec(line.trim());
    if (!match) return [];
    const [, score = "X", players = ""] = match;
    const guesses = score === "X" ? null : Number(score);
    return [...players.matchAll(MENTION)].map(([, userId = ""]) => ({ userId, guesses }));
  });
  if (results.length === 0) return undefined;
  const puzzleDate = new Date(postedAt.getTime() - DAY_MS).toISOString().slice(0, 10);
  return { puzzleDate, results };
}
