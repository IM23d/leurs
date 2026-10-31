import { integer, sqliteTable, text } from "drizzle-orm/sqlite-core";

/** Google searches per UTC day, for the global daily limit. */
export const imageSearchDays = sqliteTable("image_search_days", {
  day: text().primaryKey(),
  searches: integer().notNull(),
});

/** When each user last searched, for the per-user cooldown. */
export const imageCooldowns = sqliteTable("image_cooldowns", {
  userId: text().primaryKey(),
  searchedAt: integer({ mode: "timestamp_ms" }).notNull(),
});
