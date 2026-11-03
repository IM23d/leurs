import { expect, it } from "vitest";

import { useTestDb } from "#test/helpers/db.ts";

import { groupStats, saveSummary } from "./wordle.service.ts";

useTestDb();

it("stores summaries once and sums up the group", () => {
  const summary = {
    puzzleDate: "2026-10-27",
    results: [
      { userId: "a", guesses: 4 },
      { userId: "b", guesses: null },
    ],
  };
  expect(saveSummary("g", summary)).toBe(2);
  expect(saveSummary("g", summary)).toBe(0);
  expect(groupStats("g")).toMatchObject({ days: 1, games: 2, solved: 1 });
  expect(groupStats("other").games).toBe(0);
});
