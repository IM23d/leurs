import { describe, expect, it } from "vitest";

import { listAutoReactions } from "#modules/tools/auto-reactions.service.ts";
import { useTestDb } from "#test/helpers/db.ts";

import type { LegacySource } from "./source.ts";
import { toolsImporter } from "./tools.ts";

useTestDb();

const guild = "100000000000000001";

const sourceOf = (files: Record<string, unknown>): LegacySource => ({
  read: (file) => files[file],
});

describe("toolsImporter", () => {
  it("imports auto reactions and skips malformed entries", () => {
    const rows = toolsImporter.run(
      sourceOf({
        "auto_reactions.json": {
          [guild]: { Hello: "👋", cat: "not an emoji", dog: 5 },
          "not a guild": { hi: "👋" },
        },
      }),
    );
    expect(rows).toBe(1);
    expect(listAutoReactions(guild)).toEqual([{ guildId: guild, term: "hello", emoji: "👋" }]);
  });

  it("imports nothing when the file is missing", () => {
    expect(toolsImporter.run(sourceOf({}))).toBe(0);
  });
});
