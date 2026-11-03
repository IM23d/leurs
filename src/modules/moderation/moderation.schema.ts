import { index, integer, sqliteTable, text, uniqueIndex } from "drizzle-orm/sqlite-core";

/** Warnings, bans, kicks, mutes and jails. A null moderator means automod or an imported row. */
export const modActions = sqliteTable(
  "mod_actions",
  {
    id: integer().primaryKey({ autoIncrement: true }),
    guildId: text().notNull(),
    userId: text().notNull(),
    moderatorId: text(),
    action: text().notNull(),
    reason: text(),
    durationMs: integer(),
    createdAt: integer({ mode: "timestamp_ms" }).notNull(),
  },
  (table) => [index("mod_actions_member").on(table.guildId, table.userId)],
);

/** Each nickname change, so a member can revert to the one before. Null means no nickname. */
export const nicknameHistory = sqliteTable(
  "nickname_history",
  {
    id: integer().primaryKey({ autoIncrement: true }),
    guildId: text().notNull(),
    userId: text().notNull(),
    oldNickname: text(),
    newNickname: text(),
    createdAt: integer({ mode: "timestamp_ms" }).notNull(),
  },
  (table) => [index("nickname_history_member").on(table.guildId, table.userId)],
);

export const blockedTerms = sqliteTable(
  "blocked_terms",
  {
    id: integer().primaryKey({ autoIncrement: true }),
    guildId: text().notNull(),
    term: text().notNull(),
    punishment: text({ enum: ["warn", "mute", "kick", "ban"] }).notNull(),
    /** How long a mute or ban lasts. Null bans are permanent. */
    durationMs: integer(),
    /** Shown to the member instead of the default reason. */
    customText: text(),
    /** Matches after removing accents, digits, symbols and repeated letters. */
    advanced: integer({ mode: "boolean" }).notNull().default(false),
    addedById: text(),
    createdAt: integer({ mode: "timestamp_ms" }).notNull(),
  },
  (table) => [uniqueIndex("blocked_terms_guild_term").on(table.guildId, table.term)],
);

export type ModAction = typeof modActions.$inferSelect;
export type BlockedTerm = typeof blockedTerms.$inferSelect;
export type Punishment = BlockedTerm["punishment"];
