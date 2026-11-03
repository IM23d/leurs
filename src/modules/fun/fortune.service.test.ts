import { expect, it } from "vitest";

import { parseFortune } from "./fortune.service.ts";

it("reads the fortune text", () => {
  expect(parseFortune({ text: "Big journeys begin with a single step.", numbers: "1, 2" })).toBe(
    "Big journeys begin with a single step.",
  );
});

it("turns escaped quotes into quote characters", () => {
  expect(parseFortune({ text: String.raw`It’s “yours”` })).toBe(`It's "yours"`);
});

it.each([undefined, {}, { text: "  " }, { text: 42 }])("rejects %j", (json) => {
  expect(parseFortune(json)).toBeUndefined();
});
