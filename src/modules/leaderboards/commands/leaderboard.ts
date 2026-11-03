import { defineCommand, subcommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";

import type { BoardName } from "../boards.ts";
import { leaderboardPages } from "../leaderboard-pages.ts";

const board = (name: BoardName, description: string, aliases: readonly string[]) =>
  subcommand({
    description,
    aliases,
    options: { page: opt.integer("Page number").min(1).optional() },
    run: async (ctx, { page }) => {
      await leaderboardPages.reply(ctx, { page: page ?? 1, args: [name] });
    },
  });

export const leaderboardCommand = defineCommand({
  name: "leaderboard",
  description: "Show the top members of this server",
  aliases: ["lb", "top"],
  defaultSubcommand: "levels",
  subcommands: {
    levels: board("levels", "Top members by level", ["leveltop", "lvltop"]),
    voice: board("voice", "Top members by time in voice", ["voicelevels", "voicetop", "vtop"]),
    money: board("money", "Top members by balance", ["balancetop", "baltop"]),
  },
});
