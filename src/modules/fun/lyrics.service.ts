import { readdir, readFile } from "node:fs/promises";
import path from "node:path";

import { UserError } from "#core/errors.ts";

/** Mounted into the container at runtime. The files are not in git. */
const LYRICS_DIR = new URL("../../../assets/fun/lyrics/", import.meta.url);

/** Reads a random .txt file from `dir`. */
export async function randomLyric(
  dir: URL = LYRICS_DIR,
  random: () => number = Math.random,
): Promise<string> {
  const files = await readdir(dir).catch(() => [] as string[]);
  const lyrics = files.filter((file) => path.extname(file) === ".txt").toSorted();
  const file = lyrics[Math.floor(random() * lyrics.length)];
  if (file === undefined) throw new UserError("No lyrics are set up.");
  return readFile(new URL(file, dir), "utf8");
}
