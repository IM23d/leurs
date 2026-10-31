import { defineCommand, subcommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";

import { IMAGE_SIZE, imageEmbed } from "../profile.views.ts";

// Banners are only sent when a user or member is fetched directly, so both lookups force a fetch.
export const bannerCommand = defineCommand({
  name: "banner",
  description: "Show a member's banner",
  defaultSubcommand: "global",
  subcommands: {
    global: subcommand({
      description: "Show a user's main banner",
      options: { user: opt.user("Whose banner").optional() },
      run: async (ctx, { user }) => {
        const target = await ctx.client.users.fetch((user ?? ctx.user).id, { force: true });
        const url = target.bannerURL({ size: IMAGE_SIZE });
        if (!url) throw new UserError(`${target.displayName} doesn't have a banner.`);
        await ctx.reply(imageEmbed(`${target.displayName}'s banner`, url));
      },
    }),
    server: subcommand({
      description: "Show a member's banner for this server",
      aliases: ["sbanner"],
      options: { user: opt.member("Whose server banner").optional() },
      run: async (ctx, { user }) => {
        const member = await ctx.guild.members.fetch({
          user: (user ?? ctx.member).id,
          force: true,
        });
        const url = member.bannerURL({ size: IMAGE_SIZE });
        if (!url) throw new UserError(`${member.displayName} doesn't have a server banner.`);
        await ctx.reply(imageEmbed(`${member.displayName}'s server banner`, url));
      },
    }),
  },
});
