import { PermissionFlagsBits } from "discord.js";

import { defineCommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";
import { successEmbed } from "#shared/ui/embeds.ts";

import { asBot, assertCanModerate } from "../guards.ts";
import { logModAction } from "../mod-log.ts";

export const unmuteCommand = defineCommand({
  name: "unmute",
  description: "End a member's timeout",
  permissions: PermissionFlagsBits.ModerateMembers,
  options: { user: opt.member("Who to unmute") },
  run: async (ctx, { user }) => {
    assertCanModerate(ctx, user);
    if (!user.isCommunicationDisabled()) throw new UserError(`${user.toString()} is not muted.`);
    await asBot("time out members", () => user.timeout(null));
    await ctx.reply(successEmbed(`${user.toString()} was unmuted.`).setTitle("Member unmuted"));
    await logModAction(ctx.guild, { title: "Unmute", target: user.user, moderator: ctx.user });
  },
});
