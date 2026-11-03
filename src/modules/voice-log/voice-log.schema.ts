import { index, integer, sqliteTable, text } from "drizzle-orm/sqlite-core";

/** One row per stay in a voice channel. `leftAt` is null while the member is still there. */
export const voiceStays = sqliteTable(
  "voice_stays",
  {
    id: integer().primaryKey({ autoIncrement: true }),
    guildId: text().notNull(),
    channelId: text().notNull(),
    userId: text().notNull(),
    joinedAt: integer({ mode: "timestamp_ms" }).notNull(),
    leftAt: integer({ mode: "timestamp_ms" }),
    /** Last time the bot saw the stay running. Ends stays that were open when the bot went down. */
    lastSeenAt: integer({ mode: "timestamp_ms" }).notNull(),
  },
  (table) => [
    index("voice_stays_guild_joined").on(table.guildId, table.joinedAt),
    index("voice_stays_open").on(table.guildId, table.leftAt),
  ],
);

export type VoiceStay = typeof voiceStays.$inferSelect;
