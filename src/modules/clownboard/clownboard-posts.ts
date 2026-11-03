import type { Message, MessageReaction, PartialMessageReaction } from "discord.js";

import { savePost, type ClownboardPost, type ClownboardSettings } from "./clownboard.service.ts";
import { boardContent, boardMessage } from "./clownboard.views.ts";

/** Votes that count: no bots, and not the author voting on their own message. */
export async function countVotes(
  reaction: MessageReaction | PartialMessageReaction,
  message: Message,
): Promise<number> {
  const users = await reaction.users.fetch();
  return users.filter((user) => !user.bot && user.id !== message.author.id).size;
}

/**
 * Posts the message to the clownboard once it has enough votes, or updates the counter on a post
 * that exists. Posts stay up when votes are taken back.
 */
export async function refreshPost(
  message: Message<true>,
  post: ClownboardPost,
  settings: ClownboardSettings,
  count: number,
): Promise<void> {
  const board = message.guild.channels.cache.get(settings.channelId);
  if (!board?.isSendable()) return;
  if (post.boardMessageId !== null) {
    const sent = await board.messages.fetch(post.boardMessageId).catch(() => undefined);
    await sent?.edit({ content: boardContent(message, settings.emoji, count) });
    savePost({ ...post, count });
    return;
  }
  if (count < settings.threshold) {
    savePost({ ...post, count });
    return;
  }
  const sent = await board.send(boardMessage(message, settings.emoji, count));
  savePost({ ...post, count, boardMessageId: sent.id });
}
