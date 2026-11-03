import {
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle,
  EmbedType,
  type EmbedBuilder,
  type Message,
} from "discord.js";

import { formatDuration } from "#shared/lib/duration.ts";
import { truncate } from "#shared/lib/text.ts";
import { embed } from "#shared/ui/embeds.ts";

import type { ClownboardSettings } from "./clownboard.service.ts";

const DESCRIPTION_LIMIT = 4096;

/** The first image in the message, from an attachment or an embed. */
/** A GIF link (Tenor, Giphy, Klipy…) shows as a looping video, which an embed cannot hold. */
const gifLinkOf = (message: Message) =>
  message.embeds.find((item) => item.data.type === EmbedType.GIFV)?.url ?? undefined;

/** The first picture in the message, from an attachment or a link preview. */
const imageOf = (message: Message) =>
  message.attachments.find((file) => file.contentType?.startsWith("image/"))?.url ??
  message.embeds
    .filter((item) => item.data.type !== EmbedType.GIFV)
    .map((item) => item.image?.url ?? item.thumbnail?.url)
    .find((url) => url !== undefined);

/**
 * The text above the card: the counter, and a GIF link so Discord plays the GIF below the post.
 * Used when posting and when the counter changes, so the GIF stays.
 */
export function boardContent(message: Message, emoji: string, count: number): string {
  const gif = gifLinkOf(message);
  return [counterLine(emoji, count, message.channelId), ...(gif ? [gif] : [])].join("\n");
}

/** The clownboard post for `message`. The counter line is edited as clowns come in. */
export function boardMessage(message: Message<true>, emoji: string, count: number) {
  const author = message.member?.displayName ?? message.author.displayName;
  // A message that is only the GIF link would repeat it, so the card then has no text.
  const text = message.content.trim() === gifLinkOf(message) ? "" : message.content;
  const card = embed(text ? truncate(text, DESCRIPTION_LIMIT) : undefined)
    .setAuthor({ name: author, iconURL: message.author.displayAvatarURL() })
    .setTimestamp(message.createdAt);
  const image = imageOf(message);
  if (image) card.setImage(image);
  return {
    content: boardContent(message, emoji, count),
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

const counterLine = (emoji: string, count: number, channelId: string): string =>
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
      `**Votes needed:** ${settings.threshold}`,
      `**Cooldown:** ${cooldown} between starting votes (admins have none)`,
      "",
      `React with ${settings.emoji} to vote, or reply to a message with \`.cb\` to start a vote.`,
    ].join("\n"),
  ).setTitle("Clownboard");
}

export function topEmbed(rows: readonly { authorId: string; posts: number }[], emoji: string) {
  const lines = rows.map((row, index) => `${index + 1}. <@${row.authorId}> ${emoji} ${row.posts}`);
  return embed(lines.length > 0 ? lines.join("\n") : "Nobody has been clowned yet.").setTitle(
    "Biggest clowns",
  );
}
