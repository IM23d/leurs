import { integer, primaryKey, sqliteTable, text } from "drizzle-orm/sqlite-core";

/** One player's result for one day's puzzle, read from the Wordle app's daily summary. */
export const wordleResults = sqliteTable(
  "wordle_results",
  {
    guildId: text().notNull(),
    /** The puzzle's day as "YYYY-MM-DD". The summary posted on a day covers the day before. */
    puzzleDate: text().notNull(),
    userId: text().notNull(),
    /** Guesses needed, 1 to 6. Null for an unsolved game (X/6). */
    guesses: integer(),
  },
  (table) => [primaryKey({ columns: [table.guildId, table.puzzleDate, table.userId] })],
);

export type WordleResult = typeof wordleResults.$inferSelect;
