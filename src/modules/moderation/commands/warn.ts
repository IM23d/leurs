import { PermissionFlagsBits } from "discord.js";

import { defineCommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { warningEmbed } from "#shared/ui/embeds.ts";

import { recordAction } from "../actions.service.ts";
import { assertCanModerate } from "../guards.ts";
import { logModAction } from "../mod-log.ts";

export const warnCommand = defineCommand({
  name: "warn",
  description: "Warn a member",
  permissions: PermissionFlagsBits.ModerateMembers,
  options: {
    user: opt.member("Who to warn"),
    reason: opt.string("Why").rest().max(1000),
  },
  run: async (ctx, { user, reason }) => {
    assertCanModerate(ctx, user);
    recordAction({
      guildId: ctx.guild.id,
      userId: user.id,
      moderatorId: ctx.user.id,
      action: "warn",
      reason,
    });
    const dm = warningEmbed(`You were warned in **${ctx.guild.name}**.`)
      .setTitle("Warning")
      .addFields({ name: "Reason", value: reason });
    const dmSent = await user
      .send({ embeds: [dm] })
      .then(() => true)
      .catch(() => false);
    const reply = warningEmbed(`${user.toString()} was warned.`)
      .setTitle("Member warned")
      .addFields({ name: "Reason", value: reason });
    if (!dmSent) reply.setFooter({ text: "I couldn't DM them, their DMs are closed." });
    await ctx.reply(reply);
    await logModAction(ctx.guild, {
      title: "Warning",
      target: user.user,
      moderator: ctx.user,
      reason,
    });
  },
});
