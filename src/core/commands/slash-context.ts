import { MessageFlags, type ChatInputCommandInteraction, type Message } from "discord.js";

import { UserError } from "../errors.ts";

import { toReplyOptions, type CommandContext, type Reply } from "./context.ts";
import type { Command } from "./define.ts";

export function slashContext(
  interaction: ChatInputCommandInteraction<"cached">,
  commands: readonly Command[],
): CommandContext {
  const { channel } = interaction;
  if (!channel) throw new UserError("I can't see this channel. Check my permissions here.");
  const send = async (reply: Reply): Promise<Message> => {
    const { private: isPrivate, ...options } = toReplyOptions(reply);
    const flags = isPrivate ? MessageFlags.Ephemeral : undefined;
    if (interaction.deferred && !interaction.replied) {
      return interaction.editReply(options);
    }
    if (interaction.replied) {
      return interaction.followUp({ ...options, ...(flags === undefined ? {} : { flags }) });
    }
    const response = await interaction.reply({
      ...options,
      ...(flags === undefined ? {} : { flags }),
      withResponse: true,
    });
    const message = response.resource?.message;
    return message ?? interaction.fetchReply();
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
    reply: send,
    defer: async () => {
      if (!interaction.deferred && !interaction.replied) await interaction.deferReply();
    },
    referencedMessage: () => Promise.resolve(undefined),
  };
}
