import { PermissionFlagsBits } from "discord.js";

import { defineCommand, subcommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { successEmbed } from "#shared/ui/embeds.ts";

import { coins } from "../economy.views.ts";
import { addBalance, takeUpTo } from "../wallet.service.ts";

const options = {
  user: opt.user("Whose balance"),
  amount: opt.integer("How many coins").min(1),
};

export const moneyCommand = defineCommand({
  name: "money",
  description: "Add or remove a member's coins",
  permissions: PermissionFlagsBits.Administrator,
  subcommands: {
    add: subcommand({
      description: "Give a member coins",
      aliases: ["addbalance"],
      options,
      run: async (ctx, { user, amount }) => {
        const balance = addBalance(user.id, amount);
        await ctx.reply(
          successEmbed(`Added ${coins(amount)} to <@${user.id}>. They have ${coins(balance)}.`),
        );
      },
    }),
    remove: subcommand({
      description: "Take coins from a member, down to zero",
      aliases: ["removebalance"],
      options,
      run: async (ctx, { user, amount }) => {
        const { taken, balance } = takeUpTo(user.id, amount);
        await ctx.reply(
          successEmbed(`Removed ${coins(taken)} from <@${user.id}>. They have ${coins(balance)}.`),
        );
      },
    }),
  },
});
