import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { expect, it } from "vitest";

import { legacySource } from "./source.ts";

it("keeps Discord IDs written as JSON numbers exact", () => {
  const directory = mkdtempSync(join(tmpdir(), "leurs-legacy-"));
  writeFileSync(join(directory, "ids.json"), '{"guild": 1225863450308378644, "count": 5}');
  writeFileSync(join(directory, "empty.json"), "  ");
  const source = legacySource(directory);
  expect(source.read("ids.json")).toEqual({ guild: "1225863450308378644", count: 5 });
  expect(source.read("empty.json")).toBeUndefined();
  expect(source.read("missing.json")).toBeUndefined();
});
