import { defineCommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";

import { parseAmount } from "../amount.ts";
import { gambleEmbed } from "../economy.views.ts";
import { gamble } from "../gamble.service.ts";

export const gambleCommand = defineCommand({
  name: "gamble",
  description: "Bet coins on a coin flip",
  options: {
    amount: opt.custom("Coins, a percentage like 50%, or all", "amount", parseAmount),
  },
  run: async (ctx, { amount }) => {
    await ctx.reply(gambleEmbed(gamble(ctx.user.id, amount)));
  },
});
