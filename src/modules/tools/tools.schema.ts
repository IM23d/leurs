import { primaryKey, sqliteTable, text } from "drizzle-orm/sqlite-core";

/** The bot reacts with `emoji` to every message that contains `term`. Terms are lowercase. */
export const autoReactions = sqliteTable(
  "auto_reactions",
  {
    guildId: text().notNull(),
    term: text().notNull(),
    emoji: text().notNull(),
  },
  (table) => [primaryKey({ columns: [table.guildId, table.term] })],
);

export type AutoReaction = typeof autoReactions.$inferSelect;
