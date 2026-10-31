import { describe, expect, it } from "vitest";

import { settleLimited } from "./settle-limited.ts";

describe("settleLimited", () => {
  it("runs at most `limit` calls at once and keeps the input order", async () => {
    let running = 0;
    let peak = 0;
    const results = await settleLimited([1, 2, 3, 4, 5, 6, 7], 3, async (item) => {
      running += 1;
      peak = Math.max(peak, running);
      await new Promise((resolve) => setTimeout(resolve, 8 - item));
      running -= 1;
      if (item === 4) throw new Error("four");
      return item * 10;
    });
    expect(peak).toBe(3);
    expect(
      results.map((result) => (result.status === "fulfilled" ? result.value : "failed")),
    ).toEqual([10, 20, 30, "failed", 50, 60, 70]);
  });

  it("handles an empty list", async () => {
    await expect(settleLimited([], 4, () => Promise.resolve(1))).resolves.toEqual([]);
  });
});
