import { eq } from "drizzle-orm";

import { db } from "#db/client.ts";

import { guildSettings, type GuildSettings } from "./settings.schema.ts";

const DEFAULT_PREFIX = "-";
export const MAX_PREFIX_LENGTH = 3;

export type ChannelSetting = keyof Pick<
  GuildSettings,
  "modLogChannelId" | "blockedTermsLogChannelId" | "levelUpChannelId" | "voiceLogChannelId"
>;
export type RoleSetting = keyof Pick<GuildSettings, "jailRoleId">;

const cache = new Map<string, GuildSettings>();

const defaults = (guildId: string): GuildSettings => ({
  guildId,
  prefix: null,
  modLogChannelId: null,
  blockedTermsLogChannelId: null,
  levelUpChannelId: null,
  voiceLogChannelId: null,
  jailRoleId: null,
});

/** Reads a server's settings. Cached, because the prefix is read for every message. */
export function getSettings(guildId: string): GuildSettings {
  const cached = cache.get(guildId);
  if (cached) return cached;
  const row =
    db().select().from(guildSettings).where(eq(guildSettings.guildId, guildId)).get() ??
    defaults(guildId);
  cache.set(guildId, row);
  return row;
}

export const getPrefix = (guildId: string): string => getSettings(guildId).prefix ?? DEFAULT_PREFIX;

export function updateSettings(
  guildId: string,
  changes: Partial<Omit<GuildSettings, "guildId">>,
): GuildSettings {
  const row = db()
    .insert(guildSettings)
    .values({ ...defaults(guildId), ...changes })
    .onConflictDoUpdate({ target: guildSettings.guildId, set: changes })
    .returning()
    .get();
  cache.set(guildId, row);
  return row;
}
