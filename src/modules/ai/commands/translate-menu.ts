import { PermissionFlagsBits } from "discord.js";

import { defineContextMenu } from "#core/context-menus.ts";
import { UserError } from "#core/errors.ts";

import { takeAiRequest } from "../ai.service.ts";
import { translationEmbed } from "../ai.views.ts";
import { requireDeepseek } from "../deepseek.ts";
import { ENGLISH } from "../languages.ts";
import { messageText } from "../message-text.ts";
import { translate } from "../translation.ts";

export const translateMenu = defineContextMenu({
  type: "message",
  name: "Translate",
  run: async (interaction) => {
    requireDeepseek();
    const message = interaction.targetMessage;
    const original = messageText(message);
    if (original === undefined) throw new UserError("This message has no text to translate.");
    takeAiRequest(interaction.user.id, {
      exempt: interaction.memberPermissions.has(PermissionFlagsBits.Administrator),
      cooldown: false,
    });
    await interaction.deferReply({ flags: "Ephemeral" });
    const translation = await translate(original, ENGLISH);
    await interaction.editReply({
      embeds: [translationEmbed(translation, original, ENGLISH, message.author)],
    });
  },
});
