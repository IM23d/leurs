import { describe, expect, it } from "vitest";

import { parseColor } from "./embed-colors.ts";

describe("parseColor", () => {
  it("reads hex codes with or without #", () => {
    expect(parseColor("#FF8800")).toBe(0xff_88_00);
    expect(parseColor("00ff00")).toBe(0x00_ff_00);
  });

  it("reads the old color names", () => {
    expect(parseColor("Red")).toBe(0xe7_4c_3c);
    expect(parseColor("dark_blue")).toBe(0x20_66_94);
  });

  it("rejects anything else", () => {
    expect(parseColor("hello")).toBeUndefined();
    expect(parseColor("#fff")).toBeUndefined();
    expect(parseColor("constructor")).toBeUndefined();
  });
});
