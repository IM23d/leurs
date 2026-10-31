import type { Message, MessageReaction, PartialMessageReaction } from "discord.js";

import { getPost, savePost, type ClownboardSettings } from "./clownboard.service.ts";
import { boardMessage, counterLine } from "./clownboard.views.ts";

/** Reactions that count: no bots, and not the author clowning their own message. */
export async function countClowns(
  reaction: MessageReaction | PartialMessageReaction,
  message: Message,
): Promise<number> {
  const users = await reaction.users.fetch();
  return users.filter((user) => !user.bot && user.id !== message.author.id).size;
}

/**
 * Posts the message to the clownboard once it has enough clowns, or updates the counter on a
 * post that exists. Posts stay up when clowns are taken back.
 */
export async function refreshPost(
  message: Message<true>,
  settings: ClownboardSettings,
  count: number,
): Promise<void> {
  const board = message.guild.channels.cache.get(settings.channelId);
  if (!board?.isSendable()) return;
  const post = getPost(message.id);
  if (post) {
    const sent = await board.messages.fetch(post.boardMessageId).catch(() => undefined);
    await sent?.edit({ content: counterLine(settings.emoji, count, message.channelId) });
    savePost({ ...post, count });
    return;
  }
  if (count < settings.threshold) return;
  const sent = await board.send(boardMessage(message, settings.emoji, count));
  savePost({
    messageId: message.id,
    guildId: message.guildId,
    channelId: message.channelId,
    authorId: message.author.id,
    boardMessageId: sent.id,
    count,
    postedAt: new Date(),
  });
}
