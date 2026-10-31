import {
  PermissionFlagsBits,
  type MessageReaction,
  type PartialMessageReaction,
  type PartialUser,
  type User,
} from "discord.js";

import { takeCooldown } from "#core/cooldowns/cooldowns.ts";
import { defineEvent } from "#core/events.ts";
import { formatDuration } from "#shared/lib/duration.ts";
import { reactionEmojiKey } from "#shared/lib/emoji.ts";

import { countClowns, refreshPost } from "../clownboard-posts.ts";
import { getClownboard, getPost } from "../clownboard.service.ts";

const NOTICE_MS = 6000;

/** The clownboard settings and full message, when this reaction is a clown that matters. */
async function clownContext(
  reaction: MessageReaction | PartialMessageReaction,
  user: User | PartialUser,
) {
  const guild = reaction.message.guild;
  if (!guild || user.bot) return undefined;
  const settings = getClownboard(guild.id);
  if (!settings || reactionEmojiKey(reaction.emoji) !== settings.emojiKey) return undefined;
  if (reaction.message.channelId === settings.channelId) return undefined;
  const message = reaction.message.partial ? await reaction.message.fetch() : reaction.message;
  return message.inGuild() ? { settings, message } : undefined;
}

/** Takes the clown back and tells the member when they can clown again. */
async function rejectOnCooldown(
  reaction: MessageReaction | PartialMessageReaction,
  user: User | PartialUser,
  waitMs: number,
): Promise<void> {
  await reaction.users.remove(user.id).catch(() => undefined);
  const channel = reaction.message.channel;
  if (!channel.isSendable()) return;
  const notice = await channel.send({
    content: `<@${user.id}> you can clown again in ${formatDuration(waitMs)}.`,
    allowedMentions: { parse: [] },
  });
  setTimeout(() => void notice.delete().catch(() => undefined), NOTICE_MS);
}

export const clownAddedEvent = defineEvent({
  name: "messageReactionAdd",
  run: async (reaction, user) => {
    const context = await clownContext(reaction, user);
    if (!context) return;
    const { settings, message } = context;
    if (message.author.id === user.id) return;
    const member = await message.guild.members.fetch(user.id);
    if (!member.permissions.has(PermissionFlagsBits.Administrator)) {
      const wait = takeCooldown(`clownboard:${message.guildId}`, user.id, settings.cooldownSeconds);
      if (wait > 0) {
        await rejectOnCooldown(reaction, user, wait);
        return;
      }
    }
    await refreshPost(message, settings, await countClowns(reaction, message));
  },
});

/** Keeps the counter on an existing post right when a clown is taken back. */
export const clownRemovedEvent = defineEvent({
  name: "messageReactionRemove",
  run: async (reaction, user) => {
    const context = await clownContext(reaction, user);
    if (!context || !getPost(context.message.id)) return;
    await refreshPost(
      context.message,
      context.settings,
      await countClowns(reaction, context.message),
    );
  },
});
