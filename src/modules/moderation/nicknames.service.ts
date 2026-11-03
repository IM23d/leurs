import { and, desc, eq } from "drizzle-orm";

import { db } from "#db/client.ts";

import { nicknameHistory } from "./moderation.schema.ts";

export function recordNicknameChange(
  guildId: string,
  userId: string,
  oldNickname: string | null,
  newNickname: string | null,
  now = new Date(),
): void {
  db()
    .insert(nicknameHistory)
    .values({ guildId, userId, oldNickname, newNickname, createdAt: now })
    .run();
}

/**
 * The nickname before the latest change: a string, null for "no nickname", or undefined when
 * there is no history. Reverting records a change too, so two reverts swap back and forth.
 */
export const previousNickname = (guildId: string, userId: string): string | null | undefined =>
  db()
    .select({ oldNickname: nicknameHistory.oldNickname })
    .from(nicknameHistory)
    .where(and(eq(nicknameHistory.guildId, guildId), eq(nicknameHistory.userId, userId)))
    .orderBy(desc(nicknameHistory.createdAt), desc(nicknameHistory.id))
    .get()?.oldNickname;
