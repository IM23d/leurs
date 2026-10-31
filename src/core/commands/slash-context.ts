import { MessageFlags, type ChatInputCommandInteraction, type Message } from "discord.js";

import { UserError } from "../errors.ts";

import { toReplyOptions, type CommandContext, type Reply, type ReplyOptions } from "./context.ts";
import type { Command } from "./define.ts";

export function slashContext(
  interaction: ChatInputCommandInteraction<"cached">,
  commands: readonly Command[],
): CommandContext {
  const { channel } = interaction;
  if (!channel) throw new UserError("I can't see this channel. Check my permissions here.");
  const post = async ({ private: isPrivate, ...options }: Omit<ReplyOptions, "deleteAfter">) => {
    const flags = isPrivate ? MessageFlags.Ephemeral : undefined;
    if (interaction.deferred && !interaction.replied) return interaction.editReply(options);
    if (interaction.replied) {
      return interaction.followUp({ ...options, ...(flags === undefined ? {} : { flags }) });
    }
    const response = await interaction.reply({
      ...options,
      ...(flags === undefined ? {} : { flags }),
      withResponse: true,
    });
    return response.resource?.message ?? interaction.fetchReply();
  };

  const send = async (reply: Reply): Promise<Message> => {
    const { deleteAfter, ...options } = toReplyOptions(reply);
    const message = await post(options);
    if (deleteAfter !== undefined) {
      // deleteReply also works for private replies, which message.delete() cannot remove.
      setTimeout(
        () => void interaction.deleteReply(message).catch(() => undefined),
        deleteAfter * 1000,
      );
    }
    return message;
  };

  return {
    source: "slash",
    client: interaction.client,
    guild: interaction.guild,
    member: interaction.member,
    user: interaction.user,
    channel,
    prefix: "/",
    commands,
    messageId: undefined,
    reply: send,
    defer: async ({ private: isPrivate = false } = {}) => {
      if (interaction.deferred || interaction.replied) return;
      await interaction.deferReply(isPrivate ? { flags: MessageFlags.Ephemeral } : {});
    },
    referencedMessage: () => Promise.resolve(undefined),
  };
}
