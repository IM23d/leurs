import { MessageFlags } from "discord.js";

import { defineContextMenu } from "#core/context-menus.ts";
import { successEmbed } from "#shared/ui/embeds.ts";

import { startClownVote } from "../start-vote.ts";

/** Right-click a message, then Apps, then Clown. */
export const clownMenu = defineContextMenu({
  name: "Clown",
  type: "message",
  run: async (interaction) => {
    const text = await startClownVote(interaction.member, interaction.targetMessage);
    await interaction.reply({ embeds: [successEmbed(text)], flags: MessageFlags.Ephemeral });
  },
});
