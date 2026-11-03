import { describe, expect, it } from "vitest";

import { splitText } from "./split-text.ts";

describe("splitText", () => {
  it("keeps short text whole", () => {
    expect(splitText("  hello  ", 10)).toEqual(["hello"]);
    expect(splitText("", 10)).toEqual([]);
  });

  it("cuts at paragraphs, then lines, then spaces", () => {
    expect(splitText("aaaa bbbb\n\ncccc", 12)).toEqual(["aaaa bbbb", "cccc"]);
    expect(splitText("aaaa\nbbbb cccc", 11)).toEqual(["aaaa\nbbbb", "cccc"]);
    expect(splitText("aaaa bbbb cccc", 10)).toEqual(["aaaa bbbb", "cccc"]);
  });

  it("cuts inside a word that is longer than the limit", () => {
    expect(splitText("abcdefghij", 4)).toEqual(["abcd", "efgh", "ij"]);
  });

  it("never returns a chunk over the limit", () => {
    const text = Array.from({ length: 500 }, (_, index) => `word${index}`).join(" ");
    const chunks = splitText(text, 4096 / 8);
    expect(chunks.every((chunk) => chunk.length <= 512)).toBe(true);
    expect(chunks.join(" ")).toBe(text);
  });
});
