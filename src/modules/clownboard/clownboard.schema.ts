import { integer, sqliteTable, text } from "drizzle-orm/sqlite-core";

/** A server's clownboard. No row means the clownboard is off. */
export const clownboardSettings = sqliteTable("clownboard_settings", {
  guildId: text().primaryKey(),
  channelId: text().notNull(),
  /** As shown, e.g. "🤡" or "<:clown:123>". */
  emoji: text().notNull(),
  /** What reactions are matched on: the Unicode emoji or the custom emoji's ID. */
  emojiKey: text().notNull(),
  threshold: integer().notNull(),
  /** How long a member without Administrator waits between starting votes. */
  cooldownSeconds: integer().notNull(),
});

/**
 * Messages someone started a clown vote on. `boardMessageId` is set once enough people voted and
 * the message was posted to the clownboard.
 */
export const clownboardPosts = sqliteTable("clownboard_posts", {
  messageId: text().primaryKey(),
  guildId: text().notNull(),
  channelId: text().notNull(),
  authorId: text().notNull(),
  startedBy: text().notNull(),
  boardMessageId: text(),
  count: integer().notNull(),
  postedAt: integer({ mode: "timestamp_ms" }).notNull(),
});

export type ClownboardSettings = typeof clownboardSettings.$inferSelect;
export type ClownboardPost = typeof clownboardPosts.$inferSelect;
