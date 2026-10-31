import type { MessageReaction, PartialMessageReaction, PartialUser, User } from "discord.js";

import { defineEvent } from "#core/events.ts";
import { reactionEmojiKey } from "#shared/lib/emoji.ts";

import { countVotes, refreshPost } from "../clownboard-posts.ts";
import { getClownboard, getPost, startVote } from "../clownboard.service.ts";

/**
 * Recounts the clowns on a message. A message without a vote gets one as soon as plain reactions
 * reach the threshold, so `.cb` is a way to start a vote, not the only way.
 */
async function recount(
  reaction: MessageReaction | PartialMessageReaction,
  user: User | PartialUser,
): Promise<void> {
  const guild = reaction.message.guild;
  if (!guild || user.bot) return;
  const settings = getClownboard(guild.id);
  if (!settings || reactionEmojiKey(reaction.emoji) !== settings.emojiKey) return;
  if (reaction.message.channelId === settings.channelId) return;
  const message = reaction.message.partial ? await reaction.message.fetch() : reaction.message;
  if (!message.inGuild() || message.author.bot) return;
  const count = await countVotes(reaction, message);
  let post = getPost(message.id);
  if (!post) {
    if (count < settings.threshold) return;
    startVote({
      messageId: message.id,
      guildId: message.guildId,
      channelId: message.channelId,
      authorId: message.author.id,
      startedBy: user.id,
      postedAt: new Date(),
    });
    post = getPost(message.id);
  }
  if (post) await refreshPost(message, post, settings, count);
}

export const clownVoteAddedEvent = defineEvent({
  name: "messageReactionAdd",
  run: recount,
});

export const clownVoteRemovedEvent = defineEvent({
  name: "messageReactionRemove",
  run: recount,
});
