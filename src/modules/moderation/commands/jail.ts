import { PermissionFlagsBits } from "discord.js";

import { defineCommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { formatDuration } from "#shared/lib/duration.ts";
import { errorEmbed } from "#shared/ui/embeds.ts";

import { recordAction } from "../actions.service.ts";
import { asBot, assertCanModerate } from "../guards.ts";
import { jailRole } from "../jail-role.ts";
import { logModAction } from "../mod-log.ts";
import { NO_REASON } from "../moderation.views.ts";
import { durationOrPermanent } from "../options.ts";
import { cancelJailRelease, releaseJailTask } from "../tasks/release-jail.ts";

export const jailCommand = defineCommand({
  name: "jail",
  description: "Give a member the jail role, for a while or until unjailed",
  permissions: PermissionFlagsBits.ManageRoles,
  options: {
    user: opt.member("Who to jail"),
    duration: durationOrPermanent("How long, e.g. 30m or 7d. Leave empty for permanent").optional(),
    reason: opt.string("Why").rest().max(500).optional(),
  },
  run: async (ctx, { user, duration, reason }) => {
    assertCanModerate(ctx, user);
    const role = jailRole(ctx.guild, ctx.prefix);
    const durationMs = duration ?? undefined;
    await asBot("manage roles", () => user.roles.add(role, reason));
    // Jailing someone who is already jailed replaces the old end time.
    cancelJailRelease(ctx.guild.id, user.id);
    if (durationMs !== undefined) {
      releaseJailTask.schedule(new Date(Date.now() + durationMs), {
        guildId: ctx.guild.id,
        userId: user.id,
        roleId: role.id,
      });
    }
    recordAction({
      guildId: ctx.guild.id,
      userId: user.id,
      moderatorId: ctx.user.id,
      action: "jail",
      reason,
      durationMs,
    });
    const length =
      durationMs === undefined ? "until unjailed" : `for ${formatDuration(durationMs)}`;
    await ctx.reply(
      errorEmbed(`${user.toString()} was jailed ${length}.`)
        .setTitle("Member jailed")
        .addFields({ name: "Reason", value: reason ?? NO_REASON }),
    );
    await logModAction(ctx.guild, {
      title: "Jail",
      target: user.user,
      moderator: ctx.user,
      reason,
      durationMs,
    });
  },
});
