import { describe, expect, it } from "vitest";

import { joinWithin, truncate } from "./text.ts";

it("truncates with an ellipsis only when needed", () => {
  expect(truncate("hello", 10)).toBe("hello");
  expect(truncate("hello world", 6)).toBe("hello…");
});

describe("joinWithin", () => {
  const more = (hidden: number) => `+${hidden}`;

  it("joins everything that fits", () => {
    expect(joinWithin(["a", "b"], { limit: 100, more })).toBe("a\nb");
  });

  it("counts the entries that do not fit", () => {
    const text = joinWithin(["aaaa", "bbbb", "cccc"], { limit: 12, more });
    expect(text).toBe("aaaa\nbbbb\n+1");
    expect(text.length).toBeLessThanOrEqual(12);
  });

  it("stops at max entries", () => {
    expect(joinWithin(["a", "b", "c"], { max: 2, more })).toBe("a\nb\n+1");
  });
});
