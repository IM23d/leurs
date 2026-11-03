import type {
  GuildMember,
  MessageReaction,
  PartialMessageReaction,
  PartialUser,
  Role,
  User,
} from "discord.js";

import { reactionEmojiKey } from "#shared/lib/emoji.ts";

import { findReactionRole } from "../reaction-roles.service.ts";

/** The member and the role a reaction is about, or undefined when it is not a reaction role. */
export async function reactionRoleFor(
  reaction: MessageReaction | PartialMessageReaction,
  user: User | PartialUser,
): Promise<{ member: GuildMember; role: Role } | undefined> {
  const { guild } = reaction.message;
  const emojiKey = reactionEmojiKey(reaction.emoji);
  if (!guild || emojiKey === undefined) return undefined;
  const link = findReactionRole(guild.id, reaction.message.id, emojiKey);
  const role = link && guild.roles.cache.get(link.roleId);
  if (!role?.editable) return undefined;
  const member = await guild.members.fetch(user.id).catch(() => undefined);
  return member && !member.user.bot ? { member, role } : undefined;
}
