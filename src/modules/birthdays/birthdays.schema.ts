import { integer, sqliteTable, text } from "drizzle-orm/sqlite-core";

/** One birthday per user, shared across servers. */
export const birthdays = sqliteTable("birthdays", {
  userId: text().primaryKey(),
  year: integer().notNull(),
  month: integer().notNull(),
  day: integer().notNull(),
});
