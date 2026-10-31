import { and, eq } from "drizzle-orm";

import { db } from "#db/client.ts";

import { reactionRoles, type ReactionRole } from "./roles.schema.ts";

export type { ReactionRole } from "./roles.schema.ts";

const ofReaction = (guildId: string, messageId: string, emojiKey: string) =>
  and(
    eq(reactionRoles.guildId, guildId),
    eq(reactionRoles.messageId, messageId),
    eq(reactionRoles.emojiKey, emojiKey),
  );

/** Links an emoji on a message to a role. Replaces the role when the emoji is already linked. */
export function addReactionRole(reactionRole: ReactionRole): void {
  const { roleId, emoji, channelId } = reactionRole;
  db()
    .insert(reactionRoles)
    .values(reactionRole)
    .onConflictDoUpdate({
      target: [reactionRoles.messageId, reactionRoles.emojiKey],
      set: { roleId, emoji, channelId },
    })
    .run();
}

export function findReactionRole(
  guildId: string,
  messageId: string,
  emojiKey: string,
): ReactionRole | undefined {
  return db()
    .select()
    .from(reactionRoles)
    .where(ofReaction(guildId, messageId, emojiKey))
    .get();
}

/** Returns the removed link, or undefined when there was none. */
export function removeReactionRole(
  guildId: string,
  messageId: string,
  emojiKey: string,
): ReactionRole | undefined {
  return db()
    .delete(reactionRoles)
    .where(ofReaction(guildId, messageId, emojiKey))
    .returning()
    .get();
}

export function listReactionRoles(guildId: string): ReactionRole[] {
  return db()
    .select()
    .from(reactionRoles)
    .where(eq(reactionRoles.guildId, guildId))
    .orderBy(reactionRoles.messageId, reactionRoles.emojiKey)
    .all();
}
