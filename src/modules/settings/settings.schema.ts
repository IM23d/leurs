import { sqliteTable, text } from "drizzle-orm/sqlite-core";

/** One row per server. A missing row means every setting has its default. */
export const guildSettings = sqliteTable("guild_settings", {
  guildId: text().primaryKey(),
  prefix: text(),
  modLogChannelId: text(),
  blockedTermsLogChannelId: text(),
  levelUpChannelId: text(),
  voiceLogChannelId: text(),
  jailRoleId: text(),
});

export type GuildSettings = typeof guildSettings.$inferSelect;
