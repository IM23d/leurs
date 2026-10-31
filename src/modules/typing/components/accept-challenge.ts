import { ActionRowBuilder, ButtonBuilder, ButtonStyle } from "discord.js";

import { customId, defineComponent } from "#core/components.ts";

import { runChallenge } from "../challenge-flow.ts";
import { typingStore, type Challenge } from "../challenges.service.ts";
import { acceptedEmbed } from "../typing.views.ts";

export const acceptChallengeComponent = defineComponent({
  id: "typing-accept",
  run: async (interaction, [id = ""]) => {
    if (!interaction.isButton() || !interaction.channel) return;
    const challenge = typingStore.accept(interaction.user.id, id, interaction.guildId, Date.now());
    await interaction.update({ components: [] });
    await interaction.followUp({ embeds: [acceptedEmbed(challenge)] });
    await runChallenge(interaction.channel, challenge);
  },
});

export const acceptButton = (challenge: Challenge) =>
  new ActionRowBuilder<ButtonBuilder>().addComponents(
    new ButtonBuilder()
      .setCustomId(customId(acceptChallengeComponent, challenge.id))
      .setLabel("Accept")
      .setStyle(ButtonStyle.Success),
  );
