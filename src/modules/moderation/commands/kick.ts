import { PermissionFlagsBits } from "discord.js";

import { defineCommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { errorEmbed } from "#shared/ui/embeds.ts";

import { recordAction } from "../actions.service.ts";
import { asBot, assertCanModerate } from "../guards.ts";
import { logModAction } from "../mod-log.ts";
import { NO_REASON } from "../moderation.views.ts";

export const kickCommand = defineCommand({
  name: "kick",
  description: "Kick a member",
  permissions: PermissionFlagsBits.KickMembers,
  options: {
    user: opt.member("Who to kick"),
    reason: opt.string("Why").rest().max(500).optional(),
  },
  run: async (ctx, { user, reason }) => {
    assertCanModerate(ctx, user);
    await asBot("kick members", () => user.kick(reason));
    recordAction({
      guildId: ctx.guild.id,
      userId: user.id,
      moderatorId: ctx.user.id,
      action: "kick",
      reason,
    });
    await ctx.reply(
      errorEmbed(`${user.toString()} was kicked.`)
        .setTitle("Member kicked")
        .addFields({ name: "Reason", value: reason ?? NO_REASON }),
    );
    await logModAction(ctx.guild, {
      title: "Kick",
      target: user.user,
      moderator: ctx.user,
      reason,
    });
  },
});
