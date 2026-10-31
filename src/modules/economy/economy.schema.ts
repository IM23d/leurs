import { integer, primaryKey, sqliteTable, text } from "drizzle-orm/sqlite-core";

/** One row per user with an account. Balances are global, not per server. */
export const balances = sqliteTable("economy_balances", {
  userId: text().primaryKey(),
  balance: integer().notNull(),
});

export const ownedJobs = sqliteTable(
  "economy_owned_jobs",
  {
    userId: text().notNull(),
    job: text().notNull(),
    boughtAt: integer({ mode: "timestamp_ms" }).notNull(),
  },
  (table) => [primaryKey({ columns: [table.userId, table.job] })],
);
