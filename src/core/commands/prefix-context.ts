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
    const { private: isPrivate, deleteAfter, ...options } = toReplyOptions(reply);
    const sent = replied
      ? await channel.send(options)
      : await message.reply({
          ...options,
          allowedMentions: { parse: ["users"], repliedUser: false },
          failIfNotExists: false,
        });
    replied = true;
    const lifetime =
      deleteAfter === undefined
        ? isPrivate
          ? PRIVATE_REPLY_LIFETIME_MS
          : undefined
        : deleteAfter * 1000;
    if (lifetime !== undefined) {
      setTimeout(() => void sent.delete().catch(() => undefined), lifetime);
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
    messageId: message.id,
    reply: send,
    defer: () => channel.sendTyping(),
    referencedMessage: async () =>
      message.reference ? message.fetchReference().catch(() => undefined) : undefined,
  };
}
