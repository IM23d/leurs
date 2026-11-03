import type { Message } from "discord.js";

import { defineEvent } from "#core/events.ts";
import { getPrefix, getSettings } from "#modules/settings/api.ts";

import { recordMessage } from "../activity.service.ts";
import { levelUpEmbed } from "../levels.views.ts";

// The old bot gave no XP for commands. The registry is not reachable from a module, so any
// message that starts with the prefix or a bot mention counts as a command here.
function looksLikeCommand(message: Message<true>): boolean {
  const prefix = getPrefix(message.guildId);
  const { content } = message;
  return (
    (content.startsWith(prefix) && /^\S/.test(content.slice(prefix.length))) ||
    new RegExp(String.raw`^<@!?${message.client.user.id}>`).test(content)
  );
}

function levelUpChannel(message: Message<true>) {
  const id = getSettings(message.guildId).levelUpChannelId;
  const channel = id === null ? undefined : message.guild.channels.cache.get(id);
  return channel?.isSendable() ? channel : message.channel;
}

export const messageXpEvent = defineEvent({
  name: "messageCreate",
  run: async (message) => {
    if (message.author.bot || !message.inGuild() || looksLikeCommand(message)) return;
    const level = recordMessage(message.author.id);
    if (level === undefined) return;
    await levelUpChannel(message).send({ embeds: [levelUpEmbed(message.author, level)] });
  },
});
