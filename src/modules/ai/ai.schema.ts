import { integer, sqliteTable, text } from "drizzle-orm/sqlite-core";

/** One row per user: requests on their last day of use and when they last prompted. */
export const aiUsage = sqliteTable("ai_usage", {
  userId: text().primaryKey(),
  /** UTC day as YYYY-MM-DD. `requests` counts only this day. */
  day: text().notNull(),
  requests: integer().notNull(),
  /** Last `/ai` prompt, for the cooldown. Translations do not set it. */
  lastPromptAt: integer({ mode: "timestamp_ms" }),
});
