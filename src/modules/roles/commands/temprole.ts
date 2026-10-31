import { PermissionFlagsBits } from "discord.js";

import { defineCommand, subcommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";
import { formatDuration } from "#shared/lib/duration.ts";
import { successEmbed } from "#shared/ui/embeds.ts";

import { assertAssignable } from "../role-access.ts";
import { cancelExpiry, scheduleExpiry } from "../tasks/expire-temp-role.ts";

export const temproleCommand = defineCommand({
  name: "temprole",
  description: "Give or take a role, for good or for a while",
  permissions: PermissionFlagsBits.ManageRoles,
  subcommands: {
    add: subcommand({
      description: "Give a member a role",
      aliases: ["grant"],
      options: {
        user: opt.member("Who gets the role"),
        role: opt.role("The role to give"),
        duration: opt.duration("How long, e.g. 2h or 7d. Leave empty to keep it").optional(),
      },
      run: async (ctx, { user, role, duration }) => {
        assertAssignable(ctx, role);
        const grant = { guildId: ctx.guild.id, userId: user.id, roleId: role.id };
        const hasRole = user.roles.cache.has(role.id);
        if (!hasRole) await user.roles.add(role, `Given by ${ctx.user.tag}`);
        if (duration === undefined) {
          const hadTimer = cancelExpiry(grant) > 0;
          if (hasRole && !hadTimer) {
            throw new UserError(`${user.toString()} already has ${role.toString()}.`);
          }
        } else {
          scheduleExpiry({ ...grant, channelId: ctx.channel.id }, new Date(Date.now() + duration));
        }
        const length = duration === undefined ? "" : ` for ${formatDuration(duration)}`;
        await ctx.reply(successEmbed(`Gave ${role.toString()} to ${user.toString()}${length}.`));
      },
    }),
    remove: subcommand({
      description: "Take a role from a member",
      aliases: ["ungrant"],
      options: {
        user: opt.member("Who loses the role"),
        role: opt.role("The role to take"),
      },
      run: async (ctx, { user, role }) => {
        assertAssignable(ctx, role);
        if (!user.roles.cache.has(role.id)) {
          throw new UserError(`${user.toString()} doesn't have ${role.toString()}.`);
        }
        await user.roles.remove(role, `Taken by ${ctx.user.tag}`);
        cancelExpiry({ guildId: ctx.guild.id, userId: user.id, roleId: role.id });
        await ctx.reply(successEmbed(`Took ${role.toString()} from ${user.toString()}.`));
      },
    }),
  },
});
