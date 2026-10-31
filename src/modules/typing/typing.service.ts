import { WORDS } from "./typing.words.ts";

export const MIN_WORDS = 10;
export const MAX_WORDS = 250;
export const DEFAULT_WORDS = 30;

/** Standard typing-test convention: five characters count as one word. */
const CHARS_PER_WORD = 5;

export interface TypingResult {
  readonly wpm: number;
  readonly accuracy: number;
  readonly seconds: number;
  readonly correctChars: number;
  readonly totalChars: number;
}

export interface Comparison {
  readonly winnerId: string;
  readonly loserId: string;
  readonly winner: TypingResult;
  readonly loser: TypingResult;
  readonly wpmDiff: number;
  readonly accuracyDiff: number;
}

/** Picks `count` distinct positions from the word list, like Python's random.sample. */
export function pickWords(count: number, random: () => number = Math.random): string[] {
  const pool = [...WORDS];
  const size = Math.min(count, pool.length);
  for (let index = 0; index < size; index += 1) {
    const swap = index + Math.floor(random() * (pool.length - index));
    [pool[index], pool[swap]] = [pool[swap] ?? "", pool[index] ?? ""];
  }
  return pool.slice(0, size);
}

/**
 * Compares the typed text with the words character by character at the same position, so a
 * missed letter shifts everything after it. Spaces count as correct characters but not towards
 * the total, which is why accuracy is capped at 100.
 */
export function scoreAttempt(
  words: readonly string[],
  typed: string,
  elapsedMs: number,
): TypingResult {
  const expected = words.join(" ");
  const text = typed.trim();
  const correctChars = Array.from({ length: Math.min(expected.length, text.length) }).filter(
    (_, index) => expected[index] === text[index],
  ).length;
  const totalChars = words.reduce((sum, word) => sum + word.length, 0);
  const seconds = Math.max(elapsedMs, 1) / 1000;
  return {
    wpm: (correctChars / seconds) * (60 / CHARS_PER_WORD),
    accuracy: totalChars > 0 ? Math.min(100, (correctChars / totalChars) * 100) : 0,
    seconds,
    correctChars,
    totalChars,
  };
}

const RATINGS: readonly (readonly [number, string])[] = [
  [20, "Beginner - Keep practicing!"],
  [40, "Average - You're getting there!"],
  [60, "Good - Above average typing speed!"],
  [80, "Fast - Very good typing speed!"],
  [100, "Expert - Impressive typing skills!"],
];

export const rating = (wpm: number): string =>
  RATINGS.find(([below]) => wpm < below)?.[1] ?? "Master - Professional level typing!";

/** The challenger wins only with a strictly higher WPM, as in the old bot. */
export function compareResults(
  challenger: { id: string; result: TypingResult },
  challenged: { id: string; result: TypingResult },
): Comparison {
  const [winner, loser] =
    challenger.result.wpm > challenged.result.wpm
      ? [challenger, challenged]
      : [challenged, challenger];
  return {
    winnerId: winner.id,
    loserId: loser.id,
    winner: winner.result,
    loser: loser.result,
    wpmDiff: Math.abs(challenger.result.wpm - challenged.result.wpm),
    accuracyDiff: Math.abs(challenger.result.accuracy - challenged.result.accuracy),
  };
}

export function analysis(wpmDiff: number, winner: string, loser: string): string {
  if (wpmDiff < 5) return "A very close match! Both typists are evenly matched.";
  if (wpmDiff < 15) return `${winner} has a slight edge in typing speed.`;
  if (wpmDiff < 30) return `${winner} is notably faster than ${loser}.`;
  return `${winner} completely outclassed ${loser} in this challenge!`;
}
