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
  /** How long a member without Administrator waits between clowns. */
  cooldownSeconds: integer().notNull(),
});

/** Messages already on the clownboard, so they are posted once and their count can be updated. */
export const clownboardPosts = sqliteTable("clownboard_posts", {
  messageId: text().primaryKey(),
  guildId: text().notNull(),
  channelId: text().notNull(),
  authorId: text().notNull(),
  boardMessageId: text().notNull(),
  count: integer().notNull(),
  postedAt: integer({ mode: "timestamp_ms" }).notNull(),
});

export type ClownboardSettings = typeof clownboardSettings.$inferSelect;
export type ClownboardPost = typeof clownboardPosts.$inferSelect;
