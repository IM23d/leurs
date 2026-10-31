import { z } from "zod";

import { setUse24Hour, setZone } from "#modules/timezones/timezones.service.ts";
import { isValidZone } from "#modules/timezones/zones.ts";

import type { Importer, LegacySource } from "./source.ts";

// timezones.json: { "<userId>": "<IANA zone>" }
// timezone_preferences.json: { "<userId>": true } where true means 24-hour time
const file = z.record(z.string(), z.unknown());
const userId = z.string().regex(/^\d+$/);
const zoneEntry = z.tuple([userId, z.string().refine(isValidZone)]);
const formatEntry = z.tuple([userId, z.boolean()]);

/** Writes each valid entry of a file and returns how many it wrote. Logs how many it skipped. */
function importFile<T>(
  source: LegacySource,
  name: string,
  schema: z.ZodType<[string, T]>,
  write: (userId: string, value: T) => void,
): number {
  const entries = Object.entries(file.optional().parse(source.read(name)) ?? {});
  const valid = entries.flatMap((raw) => {
    const parsed = schema.safeParse(raw);
    return parsed.success ? [parsed.data] : [];
  });
  valid.forEach(([id, value]) => {
    write(id, value);
  });
  const skipped = entries.length - valid.length;
  if (skipped > 0) console.warn(`timezones: skipped ${skipped} malformed entries in ${name}`);
  return valid.length;
}

export const timezonesImporter: Importer = {
  name: "timezones",
  run: (source) =>
    importFile(source, "timezones.json", zoneEntry, setZone) +
    importFile(source, "timezone_preferences.json", formatEntry, setUse24Hour),
};
