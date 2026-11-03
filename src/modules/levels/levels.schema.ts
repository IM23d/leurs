import { integer, sqliteTable, text } from "drizzle-orm/sqlite-core";

/** One row per user, shared by every server like the old bot. The level is derived from xp. */
export const levels = sqliteTable("levels", {
  userId: text().primaryKey(),
  xp: integer().notNull().default(0),
  messages: integer().notNull().default(0),
  voiceSeconds: integer().notNull().default(0),
});
