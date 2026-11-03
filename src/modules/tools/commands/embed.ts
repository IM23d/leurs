import { PermissionFlagsBits } from "discord.js";

import { defineCommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";
import { embed, successEmbed } from "#shared/ui/embeds.ts";

import { openEditorRow } from "../components/embed-editor.ts";
import { parseColor } from "../embed-colors.ts";
import { customEmbed, quoteEmbed } from "../tools.views.ts";

const MAX_TEXT_LENGTH = 4096;

export const embedCommand = defineCommand({
  name: "embed",
  description: "Post text as an embed in this channel",
  permissions: PermissionFlagsBits.Administrator,
  options: {
    color: opt
      .custom("A color name or hex code, e.g. red or #ff8800", "color", parseColor)
      .optional(),
    text: opt
      .string("The embed text. Leave empty to open the editor")
      .max(MAX_TEXT_LENGTH)
      .rest()
      .optional(),
  },
  run: async (ctx, { color, text }) => {
    const replied = await ctx.referencedMessage();
    if (replied) {
      await ctx.channel.send({ embeds: [quoteEmbed(replied, text ?? replied.content, color)] });
      // The old bot replaced the replied message with the embed.
      await replied.delete().catch(() => undefined);
      return;
    }
    if (text !== undefined) {
      await ctx.channel.send({ embeds: [customEmbed({ text, color })] });
      if (ctx.source === "slash") {
        await ctx.reply({ embeds: [successEmbed("Embed posted.")], private: true });
      }
      return;
    }
    if (ctx.source === "prefix") throw new UserError("Write the text for the embed.");
    await ctx.reply({
      embeds: [embed("Write the title, text and color in the editor.")],
      components: [openEditorRow(color)],
      private: true,
    });
  },
});
