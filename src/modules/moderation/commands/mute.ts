import { PermissionFlagsBits } from "discord.js";

import { defineCommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";
import { formatDuration } from "#shared/lib/duration.ts";
import { errorEmbed } from "#shared/ui/embeds.ts";

import { checkTimeoutDuration, recordAction } from "../actions.service.ts";
import { asBot, assertCanModerate } from "../guards.ts";
import { logModAction } from "../mod-log.ts";
import { NO_REASON } from "../moderation.views.ts";

export const muteCommand = defineCommand({
  name: "mute",
  description: "Time out a member for up to 28 days",
  permissions: PermissionFlagsBits.ModerateMembers,
  options: {
    user: opt.member("Who to mute"),
    duration: opt.duration("How long, e.g. 10m or 2d"),
    reason: opt.string("Why").rest().max(500).optional(),
  },
  run: async (ctx, { user, duration, reason }) => {
    assertCanModerate(ctx, user);
    checkTimeoutDuration(duration);
    if (user.isCommunicationDisabled()) {
      throw new UserError(`${user.toString()} is already muted.`);
    }
    await asBot("time out members", () => user.timeout(duration, reason));
    recordAction({
      guildId: ctx.guild.id,
      userId: user.id,
      moderatorId: ctx.user.id,
      action: "mute",
      reason,
      durationMs: duration,
    });
    await ctx.reply(
      errorEmbed(`${user.toString()} was muted for ${formatDuration(duration)}.`)
        .setTitle("Member muted")
        .addFields({ name: "Reason", value: reason ?? NO_REASON }),
    );
    await logModAction(ctx.guild, {
      title: "Mute",
      target: user.user,
      moderator: ctx.user,
      reason,
      durationMs: duration,
    });
  },
});
