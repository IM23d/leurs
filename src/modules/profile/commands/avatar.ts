import { defineCommand, subcommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";

import { IMAGE_SIZE, imageEmbed } from "../profile.views.ts";

export const avatarCommand = defineCommand({
  name: "avatar",
  description: "Show a member's avatar",
  aliases: ["av"],
  defaultSubcommand: "global",
  subcommands: {
    global: subcommand({
      description: "Show a user's main avatar",
      options: { user: opt.user("Whose avatar").optional() },
      run: async (ctx, { user }) => {
        const target = user ?? ctx.user;
        await ctx.reply(
          imageEmbed(
            `${target.displayName}'s avatar`,
            target.displayAvatarURL({ size: IMAGE_SIZE }),
          ),
        );
      },
    }),
    server: subcommand({
      description: "Show a member's avatar for this server",
      aliases: ["serveravatar", "sav"],
      options: { user: opt.member("Whose server avatar").optional() },
      run: async (ctx, { user }) => {
        const member = user ?? ctx.member;
        const url = member.avatarURL({ size: IMAGE_SIZE });
        if (!url) throw new UserError(`${member.displayName} doesn't have a server avatar.`);
        await ctx.reply(imageEmbed(`${member.displayName}'s server avatar`, url));
      },
    }),
  },
});
