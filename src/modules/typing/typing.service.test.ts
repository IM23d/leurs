import { describe, expect, it } from "vitest";

import {
  analysis,
  compareResults,
  pickWords,
  rating,
  scoreAttempt,
  type TypingResult,
} from "./typing.service.ts";
import { WORDS } from "./typing.words.ts";

describe("scoreAttempt", () => {
  it("scores a perfect attempt", () => {
    // "the quick" has 8 letters plus a space, typed in 6 seconds.
    const result = scoreAttempt(["the", "quick"], "the quick", 6000);
    expect(result.correctChars).toBe(9);
    expect(result.totalChars).toBe(8);
    expect(result.accuracy).toBe(100);
    expect(result.seconds).toBe(6);
    expect(result.wpm).toBeCloseTo(18);
  });

  it("compares characters by position, so a missing letter shifts the rest", () => {
    const result = scoreAttempt(["abcd"], "acd", 60_000);
    expect(result.correctChars).toBe(1);
    expect(result.accuracy).toBe(25);
    expect(result.wpm).toBeCloseTo(0.2);
  });

  it("ignores surrounding whitespace", () => {
    expect(scoreAttempt(["hi"], "  hi \n", 1000).correctChars).toBe(2);
  });
});

describe("pickWords", () => {
  it("picks distinct positions from the list", () => {
    const words = pickWords(30, () => 0);
    expect(words).toHaveLength(30);
    expect(words).toEqual(WORDS.slice(0, 30));
  });

  it("never picks more words than the list has", () => {
    expect(pickWords(1000)).toHaveLength(WORDS.length);
  });
});

it.each([
  [19.9, "Beginner - Keep practicing!"],
  [20, "Average - You're getting there!"],
  [79, "Fast - Very good typing speed!"],
  [100, "Master - Professional level typing!"],
])("rates %d WPM", (wpm, expected) => {
  expect(rating(wpm)).toBe(expected);
});

const result = (wpm: number, accuracy: number): TypingResult => ({
  wpm,
  accuracy,
  seconds: 10,
  correctChars: 0,
  totalChars: 0,
});

describe("compareResults", () => {
  it("picks the faster typist and the differences", () => {
    const comparison = compareResults(
      { id: "a", result: result(50, 90) },
      { id: "b", result: result(70, 95) },
    );
    expect(comparison.winnerId).toBe("b");
    expect(comparison.loserId).toBe("a");
    expect(comparison.wpmDiff).toBe(20);
    expect(comparison.accuracyDiff).toBe(5);
  });

  it("gives a tie to the challenged user", () => {
    const comparison = compareResults(
      { id: "a", result: result(50, 90) },
      { id: "b", result: result(50, 90) },
    );
    expect(comparison.winnerId).toBe("b");
  });
});

it("describes the gap between the typists", () => {
  expect(analysis(4, "A", "B")).toBe("A very close match! Both typists are evenly matched.");
  expect(analysis(10, "A", "B")).toBe("A has a slight edge in typing speed.");
  expect(analysis(20, "A", "B")).toBe("A is notably faster than B.");
  expect(analysis(30, "A", "B")).toBe("A completely outclassed B in this challenge!");
});
