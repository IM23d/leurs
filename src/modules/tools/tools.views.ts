import type { EmbedBuilder, Message } from "discord.js";

import { embed } from "#shared/ui/embeds.ts";

import { DEFAULT_EMBED_COLOR } from "./embed-colors.ts";

export interface EmbedContent {
  readonly text: string;
  readonly title?: string | undefined;
  readonly color?: number | undefined;
}

export const customEmbed = ({ text, title, color }: EmbedContent): EmbedBuilder => {
  // An image-only message quoted by `/embed` has no text, and Discord rejects an empty description.
  const built = embed(text === "" ? undefined : text).setColor(color ?? DEFAULT_EMBED_COLOR);
  return title ? built.setTitle(title) : built;
};

/** Reposts a message as an embed under its author's name, with its first image. */
export function quoteEmbed(message: Message, text: string, color?: number): EmbedBuilder {
  const image = message.attachments.find((file) => file.contentType?.startsWith("image/"));
  const built = customEmbed({ text, color })
    .setAuthor({
      name: message.member?.displayName ?? message.author.displayName,
      iconURL: message.author.displayAvatarURL(),
    })
    .setTimestamp(message.createdAt);
  return image ? built.setImage(image.url) : built;
}
