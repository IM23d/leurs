import { integer, primaryKey, sqliteTable, text } from "drizzle-orm/sqlite-core";

/** Cooldowns of an hour or more. Shorter ones stay in memory. */
export const cooldowns = sqliteTable(
  "cooldowns",
  {
    key: text().notNull(),
    userId: text().notNull(),
    expiresAt: integer({ mode: "timestamp_ms" }).notNull(),
  },
  (table) => [primaryKey({ columns: [table.key, table.userId] })],
);
