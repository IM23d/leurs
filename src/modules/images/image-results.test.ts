import { describe, expect, it, vi } from "vitest";

import { useTestDb } from "#test/helpers/db.ts";

import { findImages } from "./image-results.ts";
import { imageUsage } from "./images.service.ts";

const NOW = Date.UTC(2026, 0, 10, 12);
const result = { title: "t", url: "u", source: "s", pageUrl: "p" };

describe("findImages", () => {
  useTestDb();

  it("searches once per query and counts only real searches", async () => {
    const search = vi.fn(() => Promise.resolve([result]));
    await findImages("Cats", true, search, NOW);
    expect(await findImages(" cats ", true, search, NOW)).toEqual([result]);
    expect(search).toHaveBeenCalledTimes(1);
    expect(imageUsage(NOW).searches).toBe(1);
  });

  it("caches SafeSearch and unfiltered results apart", async () => {
    const search = vi.fn(() => Promise.resolve([result]));
    await findImages("Dogs", true, search, NOW);
    await findImages("Dogs", false, search, NOW);
    expect(search.mock.calls).toEqual([
      ["Dogs", true],
      ["Dogs", false],
    ]);
  });
});
