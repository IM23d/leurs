import { describe, expect, it } from "vitest";

import { computeStats } from "./wordle-stats.ts";

const result = (puzzleDate: string, userId: string, guesses: number | null) => ({
  guildId: "g",
  puzzleDate,
  userId,
  guesses,
});

describe("computeStats", () => {
  const stats = computeStats([
    result("2026-10-26", "mika", 3),
    result("2026-10-26", "alex", 5),
    result("2026-10-26", "robi", null),
    result("2026-10-27", "mika", 5),
    result("2026-10-27", "alex", 5),
    result("2026-10-28", "mika", null),
    result("2026-10-28", "alex", 6),
  ]);
  const of = (userId: string) => stats.find((player) => player.userId === userId);

  it("counts games, solves, average guesses and the distribution", () => {
    expect(of("alex")).toMatchObject({
      played: 3,
      solved: 3,
      average: 16 / 3,
      distribution: [0, 0, 0, 0, 2, 1, 0],
    });
    expect(of("robi")).toMatchObject({ played: 1, solved: 0, average: undefined });
  });

  it("crowns every player with the day's best score", () => {
    expect(of("mika")?.crowns).toBe(2);
    expect(of("alex")?.crowns).toBe(2);
  });

  it("tracks streaks of solved days up to the latest puzzle", () => {
    expect(of("alex")).toMatchObject({ currentStreak: 3, bestStreak: 3 });
    expect(of("mika")).toMatchObject({ currentStreak: 0, bestStreak: 2 });
  });
});
