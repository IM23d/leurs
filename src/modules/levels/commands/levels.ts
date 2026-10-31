import { PermissionFlagsBits } from "discord.js";

import { defineCommand, subcommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";

import { setMessages } from "../levels.service.ts";
import { setMessagesEmbed } from "../levels.views.ts";

export const levelsCommand = defineCommand({
  name: "levels",
  description: "Manage member levels",
  permissions: PermissionFlagsBits.Administrator,
  subcommands: {
    set: subcommand({
      description: "Set a member's message count. XP and level follow from it",
      aliases: ["setlevel"],
      options: {
        user: opt.member("Whose level to set"),
        messages: opt.integer("Message count").min(0),
      },
      run: async (ctx, { user, messages }) => {
        await ctx.reply(setMessagesEmbed(user.user, setMessages(user.id, messages)));
      },
    }),
  },
});
