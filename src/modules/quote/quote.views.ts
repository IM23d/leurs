import { AttachmentBuilder, type Message } from "discord.js";

import { createQuote } from "./quote.service.ts";

const AVATAR_SIZE = 1024;

/** Turns a message into a quote image attachment. Uses the author's server name and avatar. */
export async function quoteAttachment(message: Message): Promise<AttachmentBuilder> {
  const author = message.member ?? message.author;
  const image = await createQuote({
    avatarUrl: author.displayAvatarURL({ extension: "png", size: AVATAR_SIZE }),
    text: message.cleanContent,
    username: author.displayName,
  });
  return new AttachmentBuilder(image, { name: "quote.png" });
}
