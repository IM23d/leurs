import { and, eq } from "drizzle-orm";

import { db } from "#db/client.ts";

import { autoReactions, type AutoReaction } from "./tools.schema.ts";

export const MAX_TERM_LENGTH = 100;

const normalize = (term: string): string => term.trim().toLowerCase();

const ofTerm = (guildId: string, term: string) =>
  and(eq(autoReactions.guildId, guildId), eq(autoReactions.term, normalize(term)));

/** Adds a term, or changes the emoji of a term that exists. */
export function setAutoReaction(guildId: string, term: string, emoji: string): AutoReaction {
  return db()
    .insert(autoReactions)
    .values({ guildId, term: normalize(term), emoji })
    .onConflictDoUpdate({ target: [autoReactions.guildId, autoReactions.term], set: { emoji } })
    .returning()
    .get();
}

/** Returns the removed entry, or undefined when the term has no auto reaction. */
export function removeAutoReaction(guildId: string, term: string): AutoReaction | undefined {
  return db().delete(autoReactions).where(ofTerm(guildId, term)).returning().get();
}

export function listAutoReactions(guildId: string): AutoReaction[] {
  return db()
    .select()
    .from(autoReactions)
    .where(eq(autoReactions.guildId, guildId))
    .orderBy(autoReactions.term)
    .all();
}

/** The emojis for every term found anywhere in the message, ignoring case. */
export function emojisFor(guildId: string, content: string): string[] {
  const text = content.toLowerCase();
  return listAutoReactions(guildId)
    .filter(({ term }) => text.includes(term))
    .map(({ emoji }) => emoji);
}
