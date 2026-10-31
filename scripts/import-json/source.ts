import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

/** Reads the JSON files of the Python bot's data/ folder. */
export interface LegacySource {
  /** Parsed JSON, or undefined when the file does not exist. */
  read(file: string): unknown;
}

type Reviver = (key: string, value: unknown, context: { source: string }) => unknown;

/**
 * Python wrote some Discord IDs as JSON numbers. Above 2^53 they lose digits as a JavaScript
 * number, so those are kept as their exact source text instead.
 */
const keepLargeIntegers: Reviver = (_key, value, context) =>
  typeof value === "number" && Number.isInteger(value) && !Number.isSafeInteger(value)
    ? context.source
    : value;

export function legacySource(directory: string): LegacySource {
  return {
    read: (file) => {
      const path = join(directory, file);
      if (!existsSync(path)) return undefined;
      const text = readFileSync(path, "utf8").trim();
      return text === ""
        ? undefined
        : (JSON.parse(text, keepLargeIntegers as Parameters<typeof JSON.parse>[1]) as unknown);
    },
  };
}

/** One module's import. Returns the number of rows written. */
export interface Importer {
  readonly name: string;
  run(source: LegacySource): number;
}
