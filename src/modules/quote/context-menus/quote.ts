import { defineContextMenu } from "#core/context-menus.ts";

import { quoteAttachment } from "../quote.views.ts";

export const quoteContextMenu = defineContextMenu({
  name: "Quote",
  type: "message",
  run: async (interaction) => {
    await interaction.deferReply();
    await interaction.editReply({ files: [await quoteAttachment(interaction.targetMessage)] });
  },
});
