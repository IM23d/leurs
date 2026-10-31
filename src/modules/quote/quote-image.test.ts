import { readFile } from "node:fs/promises";

import { describe, expect, it } from "vitest";

import { quoteLines, renderQuote } from "./quote-image.ts";

describe("quoteLines", () => {
  it("puts four words on a line inside one pair of quotes", () => {
    expect(quoteLines("one two three four five six")).toEqual(['"one two three four', 'five six"']);
    expect(quoteLines("  hi  ")).toEqual(['"hi"']);
  });
});

it("renders a PNG", async () => {
  const avatar = await readFile(new URL("../../../assets/leurs-logo.png", import.meta.url));
  const image = await renderQuote({ avatar, text: "hello there", username: "leurs" });
  expect(image.subarray(1, 4).toString()).toBe("PNG");
});
