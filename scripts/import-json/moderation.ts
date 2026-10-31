import { z } from "zod";

import { db } from "#db/client.ts";
import {
  blockedTerms,
  modActions,
  nicknameHistory,
} from "#modules/moderation/moderation.schema.ts";
import { parseDuration } from "#shared/lib/duration.ts";

import type { Importer, LegacySource } from "./source.ts";

// Python wrote datetime.utcnow().isoformat(), which has no time zone.
const timestamp = z
  .string()
  .transform((text) => new Date(/(?:Z|[+-]\d\d:?\d\d)$/.test(text) ? text : `${text}Z`))
  .refine((date) => !Number.isNaN(date.getTime()));

const text = z.string().nullish();

// Old durations are strings like "10m" or "permanent". Anything unreadable is dropped.
const durationText = text.transform((value) => (value ? (parseDuration(value) ?? null) : null));

// warnings.json: { guildId: { userId: [{ reason, timestamp }] } }
const warning = z.object({ reason: text, timestamp });

// user_actions.json: { guildId: { userId: [{ action, timestamp, reason?, duration? }] } }
const userAction = z.object({
  action: z.string(),
  timestamp,
  reason: text,
  duration: durationText,
});

// nickname_history.json: { guildId: { userId: [{ old_nick, new_nick, timestamp }] } }
const nicknameChange = z.object({ old_nick: text, new_nick: text, timestamp });

// punishments.json: { "<userId>_<guildId>": [{ type, reason, timestamp, moderator, duration }] }
const punishment = z.object({ type: z.string(), reason: text, timestamp, duration: durationText });

// blockedterms.json: { term: { punishment_type, duration (seconds), custom_text, ... } }
const blockedTerm = z.object({
  punishment_type: z.enum(["warn", "mute", "kick", "ban"]),
  duration: z.number().int().positive().nullish(),
  custom_text: text,
  advanced_filtering: z.boolean().nullish(),
  added_at: z.string().nullish(),
  guild_id: z.union([z.string(), z.number()]),
});

const perMember = z.record(z.string(), z.record(z.string(), z.array(z.unknown())));
const lists = z.record(z.string(), z.array(z.unknown()));
const objects = z.record(z.string(), z.unknown());

// SQLite limits how many values one statement may bind.
const CHUNK_SIZE = 500;

function insertInChunks<T>(rows: readonly T[], insert: (chunk: T[]) => number): number {
  return Array.from({ length: Math.ceil(rows.length / CHUNK_SIZE) }, (_, index) =>
    insert(rows.slice(index * CHUNK_SIZE, (index + 1) * CHUNK_SIZE)),
  ).reduce((sum, changes) => sum + changes, 0);
}

interface Counter {
  skipped: number;
}

/** Parses each entry on its own, so one bad entry does not stop the import. */
function each<T>(entries: readonly unknown[], schema: z.ZodType<T>, counter: Counter): T[] {
  return entries.flatMap((entry) => {
    const parsed = schema.safeParse(entry);
    if (!parsed.success) counter.skipped += 1;
    return parsed.success ? [parsed.data] : [];
  });
}

/** Reads an optional file. A file with the wrong shape counts as one skipped entry. */
function readFile<T>(
  source: LegacySource,
  file: string,
  schema: z.ZodType<T>,
  counter: Counter,
): T | undefined {
  const data = source.read(file);
  if (data === undefined) return undefined;
  const parsed = schema.safeParse(data);
  if (!parsed.success) counter.skipped += 1;
  return parsed.data;
}

interface MemberEntry<T> {
  readonly guildId: string;
  readonly userId: string;
  readonly entry: T;
}

function memberEntries<T>(
  data: z.infer<typeof perMember> | undefined,
  schema: z.ZodType<T>,
  counter: Counter,
): MemberEntry<T>[] {
  return Object.entries(data ?? {}).flatMap(([guildId, users]) =>
    Object.entries(users).flatMap(([userId, entries]) =>
      each(entries, schema, counter).map((entry) => ({ guildId, userId, entry })),
    ),
  );
}

// Large IDs arrive as strings (see source.ts), safe ones as numbers.
function guildIdFrom(value: string | number): string | undefined {
  const id = String(value);
  return /^\d{17,20}$/.test(id) ? id : undefined;
}

function importBlockedTerms(data: Record<string, unknown> | undefined, counter: Counter): number {
  const rows = Object.entries(data ?? {}).flatMap(([term, raw]) => {
    const parsed = blockedTerm.safeParse(raw);
    const guildId = parsed.success ? guildIdFrom(parsed.data.guild_id) : undefined;
    const createdAt = parsed.data?.added_at ? new Date(parsed.data.added_at) : new Date();
    if (!parsed.success || guildId === undefined || term.trim() === "") {
      counter.skipped += 1;
      return [];
    }
    const { punishment_type, duration, custom_text, advanced_filtering } = parsed.data;
    return [
      {
        guildId,
        term: term.trim(),
        punishment: punishment_type,
        durationMs: duration ? duration * 1000 : null,
        customText: custom_text ?? null,
        advanced: advanced_filtering ?? false,
        addedById: null,
        createdAt: Number.isNaN(createdAt.getTime()) ? new Date() : createdAt,
      },
    ];
  });
  return insertInChunks(
    rows,
    (chunk) => db().insert(blockedTerms).values(chunk).onConflictDoNothing().run().changes,
  );
}

function importFiles(source: LegacySource, counter: Counter): number {
  const warnings = readFile(source, "warnings.json", perMember, counter);
  const userActions = readFile(source, "user_actions.json", perMember, counter);
  const nicknames = readFile(source, "nickname_history.json", perMember, counter);
  const punishments = readFile(source, "punishments.json", lists, counter);
  const terms = readFile(source, "blockedterms.json", objects, counter);

  const punishmentEntries = Object.entries(punishments ?? {}).flatMap(([key, entries]) => {
    const [, userId, guildId] = /^(\d+)_(\d+)$/.exec(key) ?? [];
    if (userId === undefined || guildId === undefined) {
      counter.skipped += entries.length;
      return [];
    }
    return each(entries, punishment, counter).map((entry) => ({ guildId, userId, entry }));
  });

  const actions = [
    ...memberEntries(warnings, warning, counter).map(({ guildId, userId, entry }) => ({
      guildId,
      userId,
      action: "warn",
      reason: entry.reason ?? null,
      durationMs: null,
      createdAt: entry.timestamp,
    })),
    // Warnings are read from warnings.json. Older versions of the bot logged them here too.
    ...memberEntries(userActions, userAction, counter)
      .filter(({ entry }) => entry.action !== "warn")
      .map(({ guildId, userId, entry }) => ({
        guildId,
        userId,
        action: entry.action,
        reason: entry.reason ?? null,
        durationMs: entry.duration,
        createdAt: entry.timestamp,
      })),
    ...punishmentEntries.map(({ guildId, userId, entry }) => ({
      guildId,
      userId,
      action: entry.type,
      reason: entry.reason ?? null,
      durationMs: entry.duration,
      createdAt: entry.timestamp,
    })),
  ].map((row) => ({ ...row, moderatorId: null }));

  const changes = memberEntries(nicknames, nicknameChange, counter).map(
    ({ guildId, userId, entry }) => ({
      guildId,
      userId,
      oldNickname: entry.old_nick ?? null,
      newNickname: entry.new_nick ?? null,
      createdAt: entry.timestamp,
    }),
  );

  return (
    insertInChunks(actions, (chunk) => db().insert(modActions).values(chunk).run().changes) +
    insertInChunks(changes, (chunk) => db().insert(nicknameHistory).values(chunk).run().changes) +
    importBlockedTerms(terms, counter)
  );
}

export const moderationImporter: Importer = {
  name: "moderation",
  run: (source) => {
    const counter: Counter = { skipped: 0 };
    const rows = importFiles(source, counter);
    if (counter.skipped > 0) {
      console.warn(`moderation: skipped ${counter.skipped} malformed entries`);
    }
    return rows;
  },
};
