import { PermissionFlagsBits } from "discord.js";

import { defineCommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { errorEmbed } from "#shared/ui/embeds.ts";

import { recordAction } from "../actions.service.ts";
import { asBot, assertCanModerate } from "../guards.ts";
import { logModAction } from "../mod-log.ts";
import { NO_REASON } from "../moderation.views.ts";

export const banCommand = defineCommand({
  name: "ban",
  description: "Ban a member",
  permissions: PermissionFlagsBits.BanMembers,
  options: {
    user: opt.member("Who to ban"),
    reason: opt.string("Why").rest().max(500).optional(),
  },
  run: async (ctx, { user, reason }) => {
    assertCanModerate(ctx, user);
    await asBot("ban members", () => user.ban(reason === undefined ? {} : { reason }));
    recordAction({
      guildId: ctx.guild.id,
      userId: user.id,
      moderatorId: ctx.user.id,
      action: "ban",
      reason,
    });
    await ctx.reply(
      errorEmbed(`${user.toString()} was banned.`)
        .setTitle("Member banned")
        .addFields({ name: "Reason", value: reason ?? NO_REASON }),
    );
    await logModAction(ctx.guild, { title: "Ban", target: user.user, moderator: ctx.user, reason });
  },
});
