import { index, integer, sqliteTable, text } from "drizzle-orm/sqlite-core";

/** Every reaction added or removed. Discord itself only keeps the current reactions. */
export const reactionEvents = sqliteTable(
  "reaction_events",
  {
    id: integer().primaryKey({ autoIncrement: true }),
    guildId: text().notNull(),
    channelId: text().notNull(),
    messageId: text().notNull(),
    userId: text().notNull(),
    /** As Discord shows it: the Unicode emoji, or "<:name:id>" for a custom one. */
    emoji: text().notNull(),
    action: text({ enum: ["add", "remove"] }).notNull(),
    at: integer({ mode: "timestamp_ms" }).notNull(),
  },
  (table) => [
    index("reaction_events_message").on(table.messageId, table.at),
    index("reaction_events_channel").on(table.channelId, table.action, table.at),
  ],
);

export type ReactionEvent = typeof reactionEvents.$inferSelect;
