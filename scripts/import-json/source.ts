import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

/** Reads the JSON files of the Python bot's data/ folder. */
export interface LegacySource {
  /** Parsed JSON, or undefined when the file does not exist. */
  read(file: string): unknown;
}

export function legacySource(directory: string): LegacySource {
  return {
    read: (file) => {
      const path = join(directory, file);
      if (!existsSync(path)) return undefined;
      const text = readFileSync(path, "utf8").trim();
      return text === "" ? undefined : (JSON.parse(text) as unknown);
    },
  };
}

/** One module's import. Returns the number of rows written. */
export interface Importer {
  readonly name: string;
  run(source: LegacySource): number;
}
