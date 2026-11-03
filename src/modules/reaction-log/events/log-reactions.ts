import type { MessageReaction, PartialMessageReaction, PartialUser, User } from "discord.js";

import { defineEvent } from "#core/events.ts";

import { recordReaction } from "../reaction-log.service.ts";

function record(
  reaction: MessageReaction | PartialMessageReaction,
  user: User | PartialUser,
  action: "add" | "remove",
): Promise<void> {
  const { guildId, channelId, id: messageId } = reaction.message;
  if (guildId === null || user.bot || user.id === reaction.client.user.id) {
    return Promise.resolve();
  }
  recordReaction({
    guildId,
    channelId,
    messageId,
    userId: user.id,
    emoji: reaction.emoji.toString(),
    action,
    at: new Date(),
  });
  return Promise.resolve();
}

export const logReactionAdd = defineEvent({
  name: "messageReactionAdd",
  run: (reaction, user) => record(reaction, user, "add"),
});

export const logReactionRemove = defineEvent({
  name: "messageReactionRemove",
  run: (reaction, user) => record(reaction, user, "remove"),
});
