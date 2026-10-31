import { defineCommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";

import { getStats } from "../levels.service.ts";
import { rankEmbed } from "../levels.views.ts";

export const rankCommand = defineCommand({
  name: "rank",
  description: "Show a member's level, XP and voice time",
  aliases: ["level", "xp", "lvl"],
  options: { user: opt.member("Whose rank").optional() },
  run: async (ctx, { user }) => {
    const member = user ?? ctx.member;
    await ctx.reply(rankEmbed(member.user, member.displayName, getStats(member.id)));
  },
});
