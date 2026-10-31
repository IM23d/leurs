import { defineCommand } from "#core/commands/define.ts";

import { begEmbed } from "../economy.views.ts";
import { beg } from "../wallet.service.ts";

const DAY_SECONDS = 86_400;

export const begCommand = defineCommand({
  name: "beg",
  description: "Beg for a few coins once a day",
  cooldown: DAY_SECONDS,
  run: async (ctx) => {
    const { earned, balance } = beg(ctx.user.id);
    await ctx.reply(begEmbed(earned, balance));
  },
});
