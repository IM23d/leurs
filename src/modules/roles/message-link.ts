const LINK =
  /^https:\/\/(?:\w+\.)?discord(?:app)?\.com\/channels\/(\d{17,20})\/(\d{17,20})\/(\d{17,20})$/;
const ID = /^\d{17,20}$/;

export interface MessageRef {
  readonly guildId: string | undefined;
  readonly channelId: string | undefined;
  readonly messageId: string;
}

/** Reads a message link, or a bare message ID. Returns undefined for anything else. */
export function parseMessageRef(input: string): MessageRef | undefined {
  const text = input.trim();
  const link = LINK.exec(text);
  if (link) return { guildId: link[1], channelId: link[2], messageId: link[3] ?? "" };
  return ID.test(text) ? { guildId: undefined, channelId: undefined, messageId: text } : undefined;
}

export const messageLink = (guildId: string, channelId: string, messageId: string): string =>
  `https://discord.com/channels/${guildId}/${channelId}/${messageId}`;
