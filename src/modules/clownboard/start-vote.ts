import { PermissionFlagsBits, type GuildMember, type Message } from "discord.js";

import { takeCooldown } from "#core/cooldowns/cooldowns.ts";
import { UserError } from "#core/errors.ts";
import { formatDuration } from "#shared/lib/duration.ts";
import { reactionEmojiKey } from "#shared/lib/emoji.ts";

import { countVotes, refreshPost } from "./clownboard-posts.ts";
import {
  getClownboard,
  getPost,
  startVote,
  type ClownboardSettings,
} from "./clownboard.service.ts";

function checkTarget(member: GuildMember, message: Message<true>, settings: ClownboardSettings) {
  if (message.channelId === settings.channelId) {
    throw new UserError("Messages on the clownboard can't be clowned.");
  }
  if (message.author.id === member.id) throw new UserError("You can't clown your own message.");
  if (message.author.bot) throw new UserError("Bots are clowns already.");
  if (getPost(message.id)?.boardMessageId) {
    throw new UserError("That message is already on the clownboard.");
  }
}

/** Members without Administrator can start one vote per cooldown. */
function takeVoteCooldown(member: GuildMember, settings: ClownboardSettings): void {
  if (member.permissions.has(PermissionFlagsBits.Administrator)) return;
  const wait = takeCooldown(`clownboard:${member.guild.id}`, member.id, settings.cooldownSeconds);
  if (wait > 0) {
    throw new UserError(`You can start another clown vote in ${formatDuration(wait)}.`);
  }
}

/**
 * Starts a clown vote on `message`: the bot adds the clown emoji and everyone votes by clicking
 * it. The reactions already on the message count, so a message clowned before the vote started
 * goes straight onto the clownboard. Running it again on a vote only recounts. Returns the reply.
 */
export async function startClownVote(member: GuildMember, message: Message<true>): Promise<string> {
  const settings = getClownboard(member.guild.id);
  if (!settings) {
    throw new UserError(
      "The clownboard is off. An admin can turn it on with `/clownboard channel`.",
    );
  }
  checkTarget(member, message, settings);
  if (!getPost(message.id)) {
    takeVoteCooldown(member, settings);
    startVote({
      messageId: message.id,
      guildId: message.guildId,
      channelId: message.channelId,
      authorId: message.author.id,
      startedBy: member.id,
      postedAt: new Date(),
    });
  }
  await message.react(settings.emoji);
  const reaction = message.reactions.cache.find(
    (item) => reactionEmojiKey(item.emoji) === settings.emojiKey,
  );
  const count = reaction ? await countVotes(reaction, message) : 0;
  const post = getPost(message.id);
  if (post) await refreshPost(message, post, settings, count);
  return getPost(message.id)?.boardMessageId
    ? `It already had ${count} ${settings.emoji}, so it's on the clownboard now.`
    : `Clown vote running: ${count} of ${settings.threshold} ${settings.emoji}.`;
}
