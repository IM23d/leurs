import { integer, sqliteTable, text } from "drizzle-orm/sqlite-core";

/** One row per user. A user may pick a time format before setting a zone, so `zone` is nullable. */
export const timezones = sqliteTable("timezones", {
  userId: text().primaryKey(),
  zone: text(),
  use24Hour: integer({ mode: "boolean" }).notNull().default(false),
});
