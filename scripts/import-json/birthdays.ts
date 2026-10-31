import { z } from "zod";

import { parseBirthday, type CalendarDate } from "#modules/birthdays/birthday-dates.ts";
import { setBirthday } from "#modules/birthdays/birthdays.service.ts";

import type { Importer } from "./source.ts";

// birthdays.json: { "<userId>": "DD-MM-YYYY" }
const file = z.record(z.string(), z.unknown());
const entry = z.tuple([z.string().regex(/^\d+$/), z.string()]);

function readEntry(raw: [string, unknown], today: CalendarDate): [string, CalendarDate][] {
  const parsed = entry.safeParse(raw);
  if (!parsed.success) return [];
  const [userId, text] = parsed.data;
  try {
    return [[userId, parseBirthday(text, today)]];
  } catch {
    return [];
  }
}

export const birthdaysImporter: Importer = {
  name: "birthdays",
  run: (source) => {
    const now = new Date();
    const today = {
      year: now.getUTCFullYear(),
      month: now.getUTCMonth() + 1,
      day: now.getUTCDate(),
    };
    const entries = Object.entries(file.optional().parse(source.read("birthdays.json")) ?? {});
    const valid = entries.flatMap((raw) => readEntry(raw, today));
    valid.forEach(([userId, date]) => {
      setBirthday(userId, date);
    });
    const skipped = entries.length - valid.length;
    if (skipped > 0) console.warn(`birthdays: skipped ${skipped} malformed entries`);
    return valid.length;
  },
};
