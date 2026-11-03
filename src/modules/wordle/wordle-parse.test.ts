import { describe, expect, it } from "vitest";

import { parseDailySummary } from "./wordle-parse.ts";

const A = "100000000000000001";
const B = "100000000000000002";
const C = "100000000000000003";
const posted = new Date("2026-10-28T08:37:00Z");

describe("parseDailySummary", () => {
  it("reads scores, crowns, shared lines and unsolved games", () => {
    const content = `**Your group is on a 2 day streak!** 🔥 Here are yesterday's results:\n👑 5/6: <@${A}> <@${B}>\nX/6: <@${C}>`;
    expect(parseDailySummary(content, posted)).toEqual({
      puzzleDate: "2026-10-27",
      results: [
        { userId: A, guesses: 5 },
        { userId: B, guesses: 5 },
        { userId: C, guesses: null },
      ],
    });
  });

  it("ignores other Wordle messages", () => {
    expect(parseDailySummary("1 finished game of Wordle", posted)).toBeUndefined();
    expect(parseDailySummary("Here are yesterday's results:", posted)).toBeUndefined();
  });
});
