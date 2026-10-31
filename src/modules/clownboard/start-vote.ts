import { PermissionFlagsBits, type GuildMember, type Message } from "discord.js";

import { takeCooldown } from "#core/cooldowns/cooldowns.ts";
import { UserError } from "#core/errors.ts";
import { formatDuration } from "#shared/lib/duration.ts";

import { getClownboard, getPost, startVote } from "./clownboard.service.ts";

/**
 * Starts a clown vote on `message`: the bot adds the clown emoji and everyone votes by clicking
 * it. Members without Administrator can start one vote per cooldown. Returns the reply text.
 */
export async function startClownVote(member: GuildMember, message: Message<true>): Promise<string> {
  const settings = getClownboard(member.guild.id);
  if (!settings) {
    throw new UserError(
      "The clownboard is off. An admin can turn it on with `/clownboard channel`.",
    );
  }
  if (message.channelId === settings.channelId) {
    throw new UserError("Messages on the clownboard can't be clowned.");
  }
  if (message.author.id === member.id) throw new UserError("You can't clown your own message.");
  if (message.author.bot) throw new UserError("Bots are clowns already.");
  const isAdmin = member.permissions.has(PermissionFlagsBits.Administrator);
  const vote = {
    messageId: message.id,
    guildId: message.guildId,
    channelId: message.channelId,
    authorId: message.author.id,
    startedBy: member.id,
    postedAt: new Date(),
  };
  if (getPost(message.id)) throw new UserError("That message already has a clown vote.");
  if (!isAdmin) {
    const wait = takeCooldown(`clownboard:${member.guild.id}`, member.id, settings.cooldownSeconds);
    if (wait > 0) {
      throw new UserError(`You can start another clown vote in ${formatDuration(wait)}.`);
    }
  }
  startVote(vote);
  await message.react(settings.emoji);
  return `Clown vote started. It needs ${settings.threshold} ${settings.emoji} to get on the clownboard.`;
}
