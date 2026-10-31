import { PermissionFlagsBits } from "discord.js";

import { defineCommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { successEmbed } from "#shared/ui/embeds.ts";

import { MAX_PREFIX_LENGTH, updateSettings } from "../settings.service.ts";

export const prefixCommand = defineCommand({
  name: "prefix",
  description: "Change the prefix for text commands",
  permissions: PermissionFlagsBits.Administrator,
  options: { prefix: opt.string("The new prefix, e.g. - or .").max(MAX_PREFIX_LENGTH) },
  run: async (ctx, { prefix }) => {
    updateSettings(ctx.guild.id, { prefix });
    await ctx.reply(successEmbed(`Text commands now start with \`${prefix}\`.`));
  },
});
