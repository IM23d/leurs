import { defineCommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";

import { balanceEmbed } from "../economy.views.ts";
import { getBalance } from "../wallet.service.ts";

export const balanceCommand = defineCommand({
  name: "balance",
  description: "Show how many coins you or someone else has",
  aliases: ["bal"],
  options: { user: opt.user("Whose balance").optional() },
  run: async (ctx, { user }) => {
    const target = user ?? ctx.user;
    await ctx.reply(balanceEmbed(target, getBalance(target.id)));
  },
});
