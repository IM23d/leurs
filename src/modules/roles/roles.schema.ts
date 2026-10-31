import { index, integer, primaryKey, sqliteTable, text } from "drizzle-orm/sqlite-core";

/** A member's roles as of their last role change or leave. Restored when they rejoin. */
export const roleBackups = sqliteTable(
  "role_backups",
  {
    guildId: text().notNull(),
    userId: text().notNull(),
    roleIds: text({ mode: "json" }).$type<string[]>().notNull(),
    updatedAt: integer({ mode: "timestamp_ms" }).notNull(),
  },
  (table) => [primaryKey({ columns: [table.guildId, table.userId] })],
);

/** Reacting with the emoji on the message gives the role. Unreacting takes it away. */
export const reactionRoles = sqliteTable(
  "reaction_roles",
  {
    guildId: text().notNull(),
    // Unknown for messages imported from the old bot.
    channelId: text(),
    messageId: text().notNull(),
    /** A custom emoji's ID or a Unicode emoji. See parseEmoji in the tools module. */
    emojiKey: text().notNull(),
    emoji: text().notNull(),
    roleId: text().notNull(),
  },
  (table) => [
    primaryKey({ columns: [table.messageId, table.emojiKey] }),
    index("reaction_roles_guild").on(table.guildId),
  ],
);

export type ReactionRole = typeof reactionRoles.$inferSelect;
