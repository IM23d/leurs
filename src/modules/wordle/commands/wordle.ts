import { defineCommand, subcommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";

import { leaderboardMessage } from "../components/leaderboard-sort.ts";
import { isSortName, SORTS } from "../wordle-sort.ts";
import { groupStats } from "../wordle.service.ts";
import { playerEmbed } from "../wordle.views.ts";

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
      description: "Compare everyone by crowns, average guesses or games solved",
      aliases: ["wordletop"],
      options: {
        sort: opt
          .string("What to sort by")
          .choices(Object.entries(SORTS).map(([value, { label }]) => ({ name: label, value })))
          .optional(),
      },
      run: async (ctx, { sort = "crowns" }) => {
        await ctx.reply(leaderboardMessage(ctx.guild.id, isSortName(sort) ? sort : "crowns"));
      },
    }),
  },
});
