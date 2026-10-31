import type { Guild, GuildBasedChannel, GuildMember, Role } from "discord.js";

const idFrom = (text: string, pattern: RegExp): string | undefined =>
  pattern.exec(text)?.[1] ?? (/^\d{17,20}$/.test(text) ? text : undefined);

/** Resolves a member from a mention, an ID, or a username or nickname. */
export async function resolveMember(guild: Guild, text: string): Promise<GuildMember | undefined> {
  const id = idFrom(text, /^<@!?(\d{17,20})>$/);
  if (id) return guild.members.fetch(id).catch(() => undefined);
  const query = text.toLowerCase();
  const cached = guild.members.cache.find(
    (member) =>
      member.user.username.toLowerCase() === query || member.displayName.toLowerCase() === query,
  );
  if (cached) return cached;
  const found = await guild.members.fetch({ query: text, limit: 1 }).catch(() => undefined);
  return found?.first();
}

export function resolveRole(guild: Guild, text: string): Role | undefined {
  const id = idFrom(text, /^<@&(\d{17,20})>$/);
  return id
    ? guild.roles.cache.get(id)
    : guild.roles.cache.find((role) => role.name.toLowerCase() === text.toLowerCase());
}

export function resolveChannel(guild: Guild, text: string): GuildBasedChannel | undefined {
  const id = idFrom(text, /^<#(\d{17,20})>$/);
  if (id) return guild.channels.cache.get(id);
  const name = text.replace(/^#/, "").toLowerCase();
  return guild.channels.cache.find((channel) => channel.name.toLowerCase() === name);
}
