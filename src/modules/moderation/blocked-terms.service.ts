import { and, asc, eq } from "drizzle-orm";

import { UserError } from "#core/errors.ts";
import { db } from "#db/client.ts";

import { checkTimeoutDuration } from "./actions.service.ts";
import { blockedTerms, type BlockedTerm, type Punishment } from "./moderation.schema.ts";

export type { BlockedTerm, Punishment };

export const PUNISHMENTS: readonly Punishment[] = ["warn", "mute", "kick", "ban"];

/**
 * Lowercases, strips accents, digits and symbols, and collapses runs of three or more of the same
 * character, so "Hééé11!!llo" and "hello" compare equal. Same rules as the old bot.
 */
export const normalizeText = (text: string): string =>
  text
    .toLowerCase()
    .normalize("NFD")
    .replaceAll(/\p{Mn}/gu, "")
    .replaceAll(/\p{Nd}/gu, "")
    .replaceAll(/[^\p{L}\p{N}_\s]/gu, "")
    .replaceAll(/(.)\1{2,}/gu, "$1")
    .replaceAll(/\s+/g, " ")
    .trim();

/** The first term found in `content`, in the order the terms were added. */
export function matchTerm(content: string, terms: readonly BlockedTerm[]): BlockedTerm | undefined {
  const lower = content.toLowerCase();
  const normalized = normalizeText(content);
  return terms.find((term) =>
    term.advanced
      ? normalized.includes(normalizeText(term.term))
      : lower.includes(term.term.toLowerCase()),
  );
}

// The listener checks every message, so terms are cached per server.
const cache = new Map<string, BlockedTerm[]>();

export function listTerms(guildId: string): BlockedTerm[] {
  const cached = cache.get(guildId);
  if (cached) return cached;
  const rows = db()
    .select()
    .from(blockedTerms)
    .where(eq(blockedTerms.guildId, guildId))
    .orderBy(asc(blockedTerms.id))
    .all();
  cache.set(guildId, rows);
  return rows;
}

export const findBlockedTerm = (guildId: string, content: string): BlockedTerm | undefined =>
  matchTerm(content, listTerms(guildId));

interface NewTerm {
  guildId: string;
  term: string;
  punishment: Punishment;
  durationMs: number | undefined;
  customText: string | undefined;
  advanced: boolean;
  addedById: string;
}

function checkDuration(punishment: Punishment, durationMs: number | undefined): void {
  if (punishment === "mute") {
    if (durationMs === undefined) throw new UserError("A mute needs a duration.");
    checkTimeoutDuration(durationMs);
  } else if (punishment !== "ban" && durationMs !== undefined) {
    throw new UserError("Only mutes and bans take a duration.");
  }
}

/** Adds a term, or replaces the settings of a term that is already blocked. */
export function blockTerm(input: NewTerm, now = new Date()): BlockedTerm {
  checkDuration(input.punishment, input.durationMs);
  const values = {
    ...input,
    term: input.term.trim(),
    durationMs: input.durationMs ?? null,
    customText: input.customText ?? null,
    createdAt: now,
  };
  if (values.term === "") throw new UserError("The term can't be empty.");
  const row = db()
    .insert(blockedTerms)
    .values(values)
    .onConflictDoUpdate({ target: [blockedTerms.guildId, blockedTerms.term], set: values })
    .returning()
    .get();
  cache.delete(input.guildId);
  return row;
}

/** Returns false when the term was not blocked. */
export function unblockTerm(guildId: string, term: string): boolean {
  const removed =
    db()
      .delete(blockedTerms)
      .where(and(eq(blockedTerms.guildId, guildId), eq(blockedTerms.term, term.trim())))
      .run().changes > 0;
  cache.delete(guildId);
  return removed;
}

/** Forgets cached terms. Tests need it because each test starts with an empty database. */
export const clearTermCache = (): void => {
  cache.clear();
};
