import { describe, expect, it } from "vitest";

import { getStats } from "#modules/levels/levels.service.ts";
import { useTestDb } from "#test/helpers/db.ts";

import { levelsImporter } from "./levels.ts";

useTestDb();

describe("levelsImporter", () => {
  it("merges levels.json and voice_levels.json", () => {
    const files: Record<string, unknown> = {
      "levels.json": {
        "1": { xp: 3600, level: 1, total_messages: 240, last_message: 1_743_171_290.36 },
      },
      "voice_levels.json": { "1": { voice_time: 90.7 }, "2": { voice_time: 12 } },
    };
    expect(levelsImporter.run({ read: (file) => files[file] })).toBe(2);
    expect(getStats("1")).toEqual({ xp: 3600, level: 1, messages: 240, voiceSeconds: 90 });
    expect(getStats("2")).toEqual({ xp: 0, level: 0, messages: 0, voiceSeconds: 12 });
  });

  it("imports nothing when the files are missing", () => {
    expect(levelsImporter.run({ read: () => undefined })).toBe(0);
  });
});
