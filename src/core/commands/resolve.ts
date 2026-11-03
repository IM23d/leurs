import type { Guild, GuildBasedChannel, GuildMember, Role } from "discord.js";

const idFrom = (text: string, pattern: RegExp): string | undefined =>
  pattern.exec(text)?.[1] ?? (/^\d{17,20}$/.test(text) ? text : undefined);

const SEARCH_LIMIT = 10;

const isNamed = (member: GuildMember, query: string): boolean =>
  [member.user.username, member.user.globalName, member.displayName].some(
    (name) => name?.toLowerCase() === query,
  );

/**
 * Resolves a member from a mention, an ID, or an exact username or display name. Partial names
 * never match, so a moderation command cannot hit "john" when someone typed "jo".
 */
export async function resolveMember(guild: Guild, text: string): Promise<GuildMember | undefined> {
  const id = idFrom(text, /^<@!?(\d{17,20})>$/);
  if (id) return guild.members.fetch(id).catch(() => undefined);
  const query = text.toLowerCase();
  const cached = guild.members.cache.find((member) => isNamed(member, query));
  if (cached) return cached;
  const found = await guild.members
    .fetch({ query: text, limit: SEARCH_LIMIT })
    .catch(() => undefined);
  return found?.find((member) => isNamed(member, query));
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
