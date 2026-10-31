import { sqliteTable, text } from "drizzle-orm/sqlite-core";

/** Linked Last.fm accounts. Global per user, not per server. */
export const lastfmAccounts = sqliteTable("lastfm_accounts", {
  userId: text().primaryKey(),
  username: text().notNull(),
});

export type LastfmAccount = typeof lastfmAccounts.$inferSelect;
