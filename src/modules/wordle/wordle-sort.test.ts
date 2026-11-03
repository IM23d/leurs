import { expect, it } from "vitest";

import { rank } from "./wordle-sort.ts";
import type { PlayerStats } from "./wordle-stats.ts";

const player = (userId: string, crowns: number, solved: number, average?: number): PlayerStats => ({
  userId,
  played: solved + 1,
  solved,
  average,
  distribution: [],
  crowns,
  currentStreak: 0,
  bestStreak: 0,
});

const players = [player("a", 10, 50, 4.8), player("b", 30, 20, 4.5), player("c", 0, 0)];
const order = (sort: Parameters<typeof rank>[1]) => rank(players, sort).map((p) => p.userId);

it("sorts by crowns, average or solved games", () => {
  expect(order("crowns")).toEqual(["b", "a", "c"]);
  expect(order("average")).toEqual(["b", "a", "c"]);
  expect(order("solved")).toEqual(["a", "b", "c"]);
});
