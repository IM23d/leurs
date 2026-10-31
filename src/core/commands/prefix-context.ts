import type { GuildMember, Message } from "discord.js";

import { toReplyOptions, type CommandContext, type Reply } from "./context.ts";
import type { Command } from "./define.ts";

const PRIVATE_REPLY_LIFETIME_MS = 15_000;

export function prefixContext(
  message: Message<true>,
  member: GuildMember,
  prefix: string,
  commands: readonly Command[],
): CommandContext {
  const channel = message.channel;
  let replied = false;

  const send = async (reply: Reply): Promise<Message> => {
    const { private: isPrivate, ...options } = toReplyOptions(reply);
    const sent = replied
      ? await channel.send(options)
      : await message.reply({ ...options, allowedMentions: { repliedUser: false } });
    replied = true;
    if (isPrivate) {
      setTimeout(() => void sent.delete().catch(() => undefined), PRIVATE_REPLY_LIFETIME_MS);
    }
    return sent;
  };

  return {
    source: "prefix",
    client: message.client,
    guild: message.guild,
    member,
    user: message.author,
    channel,
    prefix,
    commands,
    reply: send,
    defer: () => channel.sendTyping(),
    referencedMessage: async () =>
      message.reference ? message.fetchReference().catch(() => undefined) : undefined,
  };
}
