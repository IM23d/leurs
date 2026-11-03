import type { APIEmbed, Message } from "discord.js";

import { createSnipeStore, type AttachmentInfo } from "./snipe.service.ts";

const TWO_HOURS_MS = 2 * 3_600_000;

export interface DeletedMessage {
  readonly authorName: string;
  readonly authorAvatarUrl: string;
  readonly content: string;
  readonly attachments: readonly AttachmentInfo[];
  readonly embeds: readonly APIEmbed[];
}

export const snipes = createSnipeStore<DeletedMessage>(TWO_HOURS_MS);

export const snapshot = (message: Message): DeletedMessage => ({
  authorName: message.author.username,
  authorAvatarUrl: message.author.displayAvatarURL(),
  content: message.content,
  attachments: message.attachments.map((attachment) => ({
    url: attachment.url,
    name: attachment.name,
    contentType: attachment.contentType ?? undefined,
    size: attachment.size,
  })),
  embeds: message.embeds.map((original) => original.toJSON()),
});
