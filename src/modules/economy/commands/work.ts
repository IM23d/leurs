import { defineCommand } from "#core/commands/define.ts";

import { workEmbed } from "../economy.views.ts";
import { work } from "../jobs.service.ts";

const DAY_SECONDS = 86_400;

export const workCommand = defineCommand({
  name: "work",
  description: "Work all your jobs once a day",
  cooldown: DAY_SECONDS,
  run: async (ctx) => {
    const { shifts, earned, balance } = work(ctx.user.id);
    await ctx.reply(workEmbed(shifts, earned, balance));
  },
});
