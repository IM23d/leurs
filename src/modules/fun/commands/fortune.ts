import { defineCommand } from "#core/commands/define.ts";
import { embed } from "#shared/ui/embeds.ts";

import { getFortune } from "../fortune.service.ts";

export const fortuneCommand = defineCommand({
  name: "fortune",
  description: "Break open a fortune cookie",
  aliases: ["fortunecookie", "cookie", "fc"],
  run: async (ctx) => {
    await ctx.defer();
    await ctx.reply(embed(`**${await getFortune()}**`).setTitle("🥠 Fortune cookie"));
  },
});
