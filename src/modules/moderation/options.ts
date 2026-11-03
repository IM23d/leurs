import type { Guild, GuildMember, User } from "discord.js";

import { Option, opt } from "#core/commands/options.ts";

const MENTION_OR_ID = /^(?:<@!?(\d{17,20})>|(\d{17,20}))$/;

/** Reads a mention or an ID with `fetch`, and any other text with `fallback`. */
const byId = <T>(
  base: Option<T>,
  fetch: (guild: Guild, id: string) => Promise<T>,
  fallback: (text: string, guild: Guild) => Promise<T | undefined> = () =>
    Promise.resolve(undefined),
): Option<T> =>
  new Option<T, true>(
    {
      ...base.spec,
      fromText: async (text, guild) => {
        const match = MENTION_OR_ID.exec(text);
        const id = match?.[1] ?? match?.[2];
        return id ? fetch(guild, id).catch(() => undefined) : fallback(text, guild);
      },
    },
    true,
  );

const fetchUser = (guild: Guild, id: string) => guild.client.users.fetch(id);

// `opt.member` and `opt.user` also search by name in prefix mode, so an optional one before free
// text swallows its first word: `-nick Cool Name` could rename a member called "Coolio" to "Name".
// These read only a mention or an ID.

export const mentionedMember = (description: string): Option<GuildMember> =>
  byId(opt.member(description), (guild, id) => guild.members.fetch(id));

/** Works for people who left the server, e.g. to purge their messages. */
export const mentionedUser = (description: string): Option<User> =>
  byId(opt.user(description), fetchUser);

/** Like `opt.user`, but an ID also finds people who left or were banned. */
export const anyUser = (description: string): Option<User> => {
  const base = opt.user(description);
  return byId(base, fetchUser, (text, guild) => base.spec.fromText(text, guild));
};
