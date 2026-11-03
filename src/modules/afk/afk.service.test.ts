import { describe, expect, it } from "vitest";

import { createAfkStore, formatAway } from "./afk.service.ts";

describe("afk store", () => {
  it("keeps a status until the user talks after going AFK", () => {
    const store = createAfkStore();
    store.set("1", "Lunch", 10_000);
    expect(store.get("1")).toEqual({ reason: "Lunch", since: 10_000 });
    expect(store.returnFrom("1", 9_000)).toBeUndefined();
    expect(store.returnFrom("1", 11_000)).toBeUndefined();
    expect(store.get("1")).toBeDefined();
    expect(store.returnFrom("1", 70_000)).toEqual({ reason: "Lunch", since: 10_000 });
    expect(store.get("1")).toBeUndefined();
    expect(store.returnFrom("1", 80_000)).toBeUndefined();
  });

  it("ignores users who are not AFK", () => {
    expect(createAfkStore().returnFrom("2", Date.now())).toBeUndefined();
  });
});

describe("formatAway", () => {
  it.each([
    [0, "less than a minute"],
    [59_000, "less than a minute"],
    [60_000, "1 minute"],
    [125_000, "2 minutes"],
    [3_660_000, "1 hour, 1 minute"],
  ])("formats %d ms as %s", (ms, text) => {
    expect(formatAway(ms)).toBe(text);
  });
});
