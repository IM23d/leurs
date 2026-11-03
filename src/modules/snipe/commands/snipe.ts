import { defineCommand, subcommand } from "#core/commands/define.ts";
import { UserError } from "#core/errors.ts";
import { successEmbed } from "#shared/ui/embeds.ts";

import { snipeEmbeds } from "../snipe.views.ts";
import { snipes } from "../snipes.ts";

export const snipeCommand = defineCommand({
  name: "snipe",
  description: "Show the last deleted message in this channel",
  defaultSubcommand: "show",
  subcommands: {
    show: subcommand({
      description: "Show the last deleted message in this channel",
      aliases: ["s"],
      run: async (ctx) => {
        const snipe = snipes.latest(ctx.channel.id);
        if (!snipe) throw new UserError("No recently deleted messages in this channel.");
        await ctx.reply({ embeds: snipeEmbeds(snipe) });
      },
    }),
    clear: subcommand({
      description: "Forget the last deleted message in this channel",
      aliases: ["clearsnipe", "cs"],
      run: async (ctx) => {
        snipes.clear(ctx.channel.id);
        await ctx.reply({ embeds: [successEmbed("Snipe cleared.")], private: true });
      },
    }),
  },
});
