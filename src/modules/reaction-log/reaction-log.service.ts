import { and, count, desc, eq, gte, lt } from "drizzle-orm";

import { db } from "#db/client.ts";

import { reactionEvents, type ReactionEvent } from "./reaction-log.schema.ts";

export type { ReactionEvent } from "./reaction-log.schema.ts";

/** Reaction history is kept this long. */
export const RETENTION_MS = 7 * 86_400_000;

export function recordReaction(event: Omit<ReactionEvent, "id">): void {
  db().insert(reactionEvents).values(event).run();
}

/** One page of a message's reaction changes, newest first, and how many there are. */
export function reactionHistory(
  guildId: string,
  messageId: string,
  offset: number,
  limit: number,
): { events: ReactionEvent[]; total: number } {
  const where = and(eq(reactionEvents.guildId, guildId), eq(reactionEvents.messageId, messageId));
  const events = db()
    .select()
    .from(reactionEvents)
    .where(where)
    .orderBy(desc(reactionEvents.at), desc(reactionEvents.id))
    .limit(limit)
    .offset(offset)
    .all();
  const total = db().select({ total: count() }).from(reactionEvents).where(where).get()?.total ?? 0;
  return { events, total };
}

/** The latest reaction removed in a channel since `since`. */
export function latestRemoval(channelId: string, since: Date): ReactionEvent | undefined {
  return db()
    .select()
    .from(reactionEvents)
    .where(
      and(
        eq(reactionEvents.channelId, channelId),
        eq(reactionEvents.action, "remove"),
        gte(reactionEvents.at, since),
      ),
    )
    .orderBy(desc(reactionEvents.at), desc(reactionEvents.id))
    .get();
}

export function pruneReactions(before: Date): number {
  return db().delete(reactionEvents).where(lt(reactionEvents.at, before)).run().changes;
}
