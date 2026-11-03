import { and, count, desc, eq, isNotNull, or } from "drizzle-orm";

import { db } from "#db/client.ts";

import {
  clownboardPosts,
  clownboardSettings,
  type ClownboardPost,
  type ClownboardSettings,
} from "./clownboard.schema.ts";

export type { ClownboardPost, ClownboardSettings } from "./clownboard.schema.ts";

export const DEFAULTS = {
  emoji: "🤡",
  emojiKey: "🤡",
  threshold: 3,
  cooldownSeconds: 6 * 3600,
} as const;

export function getClownboard(guildId: string): ClownboardSettings | undefined {
  return db()
    .select()
    .from(clownboardSettings)
    .where(eq(clownboardSettings.guildId, guildId))
    .get();
}

/** Turns the clownboard on in `channelId`, keeping any settings changed before. */
export function enableClownboard(guildId: string, channelId: string): ClownboardSettings {
  return db()
    .insert(clownboardSettings)
    .values({ guildId, channelId, ...DEFAULTS })
    .onConflictDoUpdate({ target: clownboardSettings.guildId, set: { channelId } })
    .returning()
    .get();
}

/** Changes settings of an enabled clownboard. Returns undefined when it is off. */
export function updateClownboard(
  guildId: string,
  changes: Partial<Omit<ClownboardSettings, "guildId" | "channelId">>,
): ClownboardSettings | undefined {
  return db()
    .update(clownboardSettings)
    .set(changes)
    .where(eq(clownboardSettings.guildId, guildId))
    .returning()
    .all()
    .at(0);
}

export function disableClownboard(guildId: string): boolean {
  return (
    db().delete(clownboardSettings).where(eq(clownboardSettings.guildId, guildId)).run().changes > 0
  );
}

export const getPost = (messageId: string): ClownboardPost | undefined =>
  db().select().from(clownboardPosts).where(eq(clownboardPosts.messageId, messageId)).get();

/** Starts a vote. Returns false when the message already has one. */
export function startVote(vote: Omit<ClownboardPost, "boardMessageId" | "count">): boolean {
  return (
    db()
      .insert(clownboardPosts)
      .values({ ...vote, boardMessageId: null, count: 0 })
      .onConflictDoNothing()
      .run().changes > 0
  );
}

/** Stores the latest vote count, and the clownboard message once it is posted. */
export function savePost(post: ClownboardPost): void {
  db()
    .update(clownboardPosts)
    .set({ count: post.count, boardMessageId: post.boardMessageId })
    .where(eq(clownboardPosts.messageId, post.messageId))
    .run();
}

/** Forgets a post. Returns it, so the caller can delete the board message. */
export function removePost(messageId: string): ClownboardPost | undefined {
  return db()
    .delete(clownboardPosts)
    .where(eq(clownboardPosts.messageId, messageId))
    .returning()
    .all()
    .at(0);
}

/** Finds a post by the original message ID or by its clownboard message ID. */
export function findPost(guildId: string, messageId: string): ClownboardPost | undefined {
  return db()
    .select()
    .from(clownboardPosts)
    .where(
      and(
        eq(clownboardPosts.guildId, guildId),
        or(eq(clownboardPosts.messageId, messageId), eq(clownboardPosts.boardMessageId, messageId)),
      ),
    )
    .get();
}

/** Members with the most messages that made it onto the clownboard. */
export function topClowns(guildId: string, limit: number): { authorId: string; posts: number }[] {
  return db()
    .select({ authorId: clownboardPosts.authorId, posts: count() })
    .from(clownboardPosts)
    .where(and(eq(clownboardPosts.guildId, guildId), isNotNull(clownboardPosts.boardMessageId)))
    .groupBy(clownboardPosts.authorId)
    .orderBy(desc(count()), clownboardPosts.authorId)
    .limit(limit)
    .all();
}
