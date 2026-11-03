import { describe, expect, it } from "vitest";

import { parseAmount, resolveAmount } from "./amount.ts";

describe("parseAmount", () => {
  it("reads coins, percentages and all", () => {
    expect(parseAmount("250")).toEqual({ kind: "coins", coins: 250 });
    expect(parseAmount("1,000")).toEqual({ kind: "coins", coins: 1000 });
    expect(parseAmount("50%")).toEqual({ kind: "percent", percent: 50 });
    expect(parseAmount("ALL")).toEqual({ kind: "all" });
  });

  it("rejects anything else", () => {
    for (const text of ["", "0", "-5", "1.5", "0%", "101%", "half", "1e3"]) {
      expect(parseAmount(text)).toBeUndefined();
    }
  });
});

describe("resolveAmount", () => {
  it("rounds percentages down", () => {
    expect(resolveAmount({ kind: "percent", percent: 33 }, 10)).toBe(3);
    expect(resolveAmount({ kind: "all" }, 10)).toBe(10);
    expect(resolveAmount({ kind: "coins", coins: 4 }, 10)).toBe(4);
  });
});
