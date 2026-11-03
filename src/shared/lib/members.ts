import type { Guild } from "discord.js";

const REFRESH_MS = 5 * 60_000;
const fetched = new Map<string, number>();

/**
 * IDs of everyone in the server. Fetches the full member list at most every five minutes,
 * because a full fetch is slow on big servers and Discord rate-limits it.
 */
export async function memberIds(guild: Guild, now = Date.now()): Promise<ReadonlySet<string>> {
  const last = fetched.get(guild.id) ?? 0;
  if (now - last > REFRESH_MS) {
    fetched.set(guild.id, now);
    await guild.members.fetch().catch(() => undefined);
  }
  return new Set(guild.members.cache.keys());
}
