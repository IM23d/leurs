import { PermissionFlagsBits } from "discord.js";

import { defineCommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";
import { successEmbed } from "#shared/ui/embeds.ts";

import { asBot, assertCanModerate } from "../guards.ts";
import { jailRole } from "../jail-role.ts";
import { logModAction } from "../mod-log.ts";
import { cancelJailRelease } from "../tasks/release-jail.ts";

export const unjailCommand = defineCommand({
  name: "unjail",
  description: "Take the jail role away from a member",
  permissions: PermissionFlagsBits.ManageRoles,
  options: { user: opt.member("Who to release") },
  run: async (ctx, { user }) => {
    assertCanModerate(ctx, user);
    const role = jailRole(ctx.guild, ctx.prefix);
    if (!user.roles.cache.has(role.id)) throw new UserError(`${user.toString()} is not jailed.`);
    await asBot("manage roles", () => user.roles.remove(role));
    cancelJailRelease(ctx.guild.id, user.id);
    await ctx.reply(
      successEmbed(`${user.toString()} was released from jail.`).setTitle("Member released"),
    );
    await logModAction(ctx.guild, { title: "Unjail", target: user.user, moderator: ctx.user });
  },
});
