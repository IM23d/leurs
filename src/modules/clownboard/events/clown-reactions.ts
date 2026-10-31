import type { MessageReaction, PartialMessageReaction, PartialUser, User } from "discord.js";

import { defineEvent } from "#core/events.ts";
import { reactionEmojiKey } from "#shared/lib/emoji.ts";

import { countVotes, refreshPost } from "../clownboard-posts.ts";
import { getClownboard, getPost } from "../clownboard.service.ts";

/** Recounts the votes when someone clicks or unclicks the clown on a message with a vote. */
async function recount(
  reaction: MessageReaction | PartialMessageReaction,
  user: User | PartialUser,
): Promise<void> {
  const guild = reaction.message.guild;
  if (!guild || user.bot) return;
  const settings = getClownboard(guild.id);
  const post = getPost(reaction.message.id);
  if (!settings || !post || reactionEmojiKey(reaction.emoji) !== settings.emojiKey) return;
  const message = reaction.message.partial ? await reaction.message.fetch() : reaction.message;
  if (!message.inGuild()) return;
  await refreshPost(message, post, settings, await countVotes(reaction, message));
}

export const clownVoteAddedEvent = defineEvent({
  name: "messageReactionAdd",
  run: recount,
});

export const clownVoteRemovedEvent = defineEvent({
  name: "messageReactionRemove",
  run: recount,
});
