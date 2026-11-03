import { EmbedBuilder } from "discord.js";

import { embed } from "#shared/ui/embeds.ts";

import { formatSize, isImage, type Snipe } from "./snipe.service.ts";
import type { DeletedMessage } from "./snipes.ts";

const MAX_FIELD_LENGTH = 1024;
// Discord allows 10 embeds per message, and the snipe itself takes one.
const MAX_ORIGINAL_EMBEDS = 9;
// Discord rejects a message whose embeds hold more than 6000 characters in total.
const MAX_TOTAL_LENGTH = 6000;

function snipeEmbed({ message, deletedAt }: Snipe<DeletedMessage>): EmbedBuilder {
  const built = embed(message.content === "" ? undefined : message.content)
    .setAuthor({ name: message.authorName, iconURL: message.authorAvatarUrl })
    .setFooter({ text: "Message deleted" })
    .setTimestamp(deletedAt);
  const image = message.attachments.find(isImage);
  if (image) built.setImage(image.url);
  if (message.attachments.length === 0) return built;
  const list = message.attachments
    .map((file) => `[${file.name}](${file.url}) (${formatSize(file.size)})`)
    .join("\n");
  return built.addFields({ name: "Attachments", value: list.slice(0, MAX_FIELD_LENGTH) });
}

/** The snipe embed followed by as many of the deleted message's own embeds as fit. */
export function snipeEmbeds(snipe: Snipe<DeletedMessage>): EmbedBuilder[] {
  const first = snipeEmbed(snipe);
  const embeds = [first];
  let total = first.length;
  for (const original of snipe.message.embeds.slice(0, MAX_ORIGINAL_EMBEDS)) {
    const copy = EmbedBuilder.from(original);
    if (total + copy.length > MAX_TOTAL_LENGTH) break;
    embeds.push(copy);
    total += copy.length;
  }
  return embeds;
}
