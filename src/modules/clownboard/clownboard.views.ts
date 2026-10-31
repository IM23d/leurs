import {
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle,
  type EmbedBuilder,
  type Message,
} from "discord.js";

import { formatDuration } from "#shared/lib/duration.ts";
import { truncate } from "#shared/lib/text.ts";
import { embed } from "#shared/ui/embeds.ts";

import type { ClownboardSettings } from "./clownboard.service.ts";

const DESCRIPTION_LIMIT = 4096;

/** The first image in the message, from an attachment or an embed. */
const imageOf = (message: Message) =>
  message.attachments.find((file) => file.contentType?.startsWith("image/"))?.url ??
  message.embeds.find((item) => item.image ?? item.thumbnail)?.image?.url;

/** The clownboard post for `message`. The counter line is edited as clowns come in. */
export function boardMessage(message: Message<true>, emoji: string, count: number) {
  const author = message.member?.displayName ?? message.author.displayName;
  const card = embed(message.content ? truncate(message.content, DESCRIPTION_LIMIT) : undefined)
    .setAuthor({ name: author, iconURL: message.author.displayAvatarURL() })
    .setTimestamp(message.createdAt);
  const image = imageOf(message);
  if (image) card.setImage(image);
  return {
    content: counterLine(emoji, count, message.channelId),
    embeds: [card],
    components: [
      new ActionRowBuilder<ButtonBuilder>().addComponents(
        new ButtonBuilder()
          .setStyle(ButtonStyle.Link)
          .setLabel("Jump to message")
          .setURL(message.url),
      ),
    ],
    allowedMentions: { parse: [] },
  };
}

export const counterLine = (emoji: string, count: number, channelId: string): string =>
  `${emoji} **${count}** · <#${channelId}>`;

export function settingsEmbed(settings: ClownboardSettings | undefined): EmbedBuilder {
  if (!settings) {
    return embed("The clownboard is off. An admin can turn it on with `/clownboard channel`.");
  }
  const cooldown =
    settings.cooldownSeconds === 0 ? "none" : formatDuration(settings.cooldownSeconds * 1000);
  return embed(
    [
      `**Channel:** <#${settings.channelId}>`,
      `**Emoji:** ${settings.emoji}`,
      `**Needed:** ${settings.threshold} ${settings.threshold === 1 ? "reaction" : "reactions"}`,
      `**Cooldown:** ${cooldown} between clowns (admins have none)`,
    ].join("\n"),
  ).setTitle("Clownboard");
}

export function topEmbed(rows: readonly { authorId: string; posts: number }[], emoji: string) {
  const lines = rows.map((row, index) => `${index + 1}. <@${row.authorId}> ${emoji} ${row.posts}`);
  return embed(lines.length > 0 ? lines.join("\n") : "Nobody has been clowned yet.").setTitle(
    "Biggest clowns",
  );
}
