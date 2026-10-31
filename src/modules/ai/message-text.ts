import type { Message } from "discord.js";

/** The text of a message, or of its first embed with a description, such as a bot's reply. */
export const messageText = (message: Message): string | undefined =>
  message.content.trim() || message.embeds.find((item) => item.description)?.description?.trim();
