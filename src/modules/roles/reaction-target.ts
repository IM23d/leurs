import type { Message } from "discord.js";

import type { CommandContext } from "#core/commands/context.ts";
import { UserError } from "#core/errors.ts";
import { embed } from "#shared/ui/embeds.ts";

import { parseMessageRef, type MessageRef } from "./message-link.ts";

const NOT_FOUND = "I can't find that message. For a message in another channel, use its link.";

/** Fetches a message from a link, or by ID from the current channel. */
export async function fetchMessage(ctx: CommandContext, ref: MessageRef): Promise<Message> {
  if (ref.guildId !== undefined && ref.guildId !== ctx.guild.id) {
    throw new UserError("That message is in another server.");
  }
  const channel =
    ref.channelId === undefined ? ctx.channel : ctx.guild.channels.cache.get(ref.channelId);
  if (!channel?.isTextBased()) throw new UserError(NOT_FOUND);
  const message = await channel.messages.fetch(ref.messageId).catch(() => undefined);
  if (!message) throw new UserError(NOT_FOUND);
  return message;
}

/**
 * The message to put a reaction role on. A link or ID picks an existing message. Any other text
 * is posted as a new message, like the old `reactrole` did.
 */
export async function reactionTarget(
  ctx: CommandContext,
  input: string,
): Promise<{ message: Message; created: boolean }> {
  const ref = parseMessageRef(input);
  return ref
    ? { message: await fetchMessage(ctx, ref), created: false }
    : { message: await ctx.channel.send({ embeds: [embed(input)] }), created: true };
}
