import { defineCommand, subcommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";

import { groupStats } from "../wordle.service.ts";
import { leaderboardEmbed, playerEmbed } from "../wordle.views.ts";

export const wordleCommand = defineCommand({
  name: "wordle",
  description: "Wordle stats from the Wordle app's daily results",
  defaultSubcommand: "stats",
  subcommands: {
    stats: subcommand({
      description: "Show a player's games, solve rate, average guesses and streaks",
      options: { user: opt.user("Whose stats").optional() },
      run: async (ctx, { user }) => {
        const player = user ?? ctx.user;
        const stats = groupStats(ctx.guild.id).players.find((p) => p.userId === player.id);
        await ctx.reply(playerEmbed(player, stats));
      },
    }),
    leaderboard: subcommand({
      description: "Compare everyone by average guesses and games solved",
      aliases: ["wordletop"],
      run: async (ctx) => {
        await ctx.reply(leaderboardEmbed(groupStats(ctx.guild.id)));
      },
    }),
  },
});
