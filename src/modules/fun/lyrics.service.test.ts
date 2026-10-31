import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

import { afterEach, beforeEach, expect, it } from "vitest";

import { randomLyric } from "./lyrics.service.ts";

let dir: string;
const dirUrl = () => pathToFileURL(`${dir}/`);

beforeEach(async () => {
  dir = await mkdtemp(path.join(tmpdir(), "lyrics-"));
});
afterEach(async () => {
  await rm(dir, { recursive: true });
});

it("reads a random .txt file", async () => {
  await writeFile(path.join(dir, "1.txt"), "first");
  await writeFile(path.join(dir, "2.txt"), "second");
  await writeFile(path.join(dir, "notes.md"), "skip me");
  expect(await randomLyric(dirUrl(), () => 0.99)).toBe("second");
});

it("explains when there are no lyrics", async () => {
  await expect(randomLyric(dirUrl())).rejects.toThrow("No lyrics are set up.");
  await expect(randomLyric(pathToFileURL(path.join(dir, "missing/")))).rejects.toThrow(
    "No lyrics are set up.",
  );
});
