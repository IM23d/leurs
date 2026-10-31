import { expect, it } from "vitest";

import { chunks } from "./chunks.ts";

it("splits a list into chunks of the given size", () => {
  expect(chunks([1, 2, 3, 4, 5], 2)).toEqual([[1, 2], [3, 4], [5]]);
  expect(chunks([], 2)).toEqual([]);
});
