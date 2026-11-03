import { PermissionFlagsBits, time, TimestampStyles } from "discord.js";

import { defineCommand, subcommand } from "#core/commands/define.ts";
import { embed, successEmbed } from "#shared/ui/embeds.ts";

import { backupRoleIds } from "../role-access.ts";
import { backupStatus, saveBackups } from "../role-backups.service.ts";

export const rolebackupCommand = defineCommand({
  name: "rolebackup",
  description: "Members get their roles back when they rejoin",
  aliases: ["saveroles"],
  permissions: PermissionFlagsBits.Administrator,
  defaultSubcommand: "status",
  subcommands: {
    status: subcommand({
      description: "Show how many members have a role backup",
      aliases: ["saveroles info"],
      run: async (ctx) => {
        const { members, lastUpdate } = backupStatus(ctx.guild.id);
        const lines = [
          `**Members with a backup**: ${members}`,
          `**Last change**: ${lastUpdate ? time(lastUpdate, TimestampStyles.RelativeTime) : "Never"}`,
          "",
          "Roles are saved when they change or a member leaves, and given back when they rejoin.",
        ];
        await ctx.reply(embed(lines.join("\n")).setTitle("Role backup"));
      },
    }),
    save: subcommand({
      description: "Back up every member's roles now",
      aliases: ["saveroles save"],
      cooldown: 60,
      run: async (ctx) => {
        await ctx.defer();
        const members = await ctx.guild.members.fetch();
        const saved = saveBackups(
          ctx.guild.id,
          members
            .filter((member) => !member.user.bot)
            .map((member) => ({ userId: member.id, roleIds: backupRoleIds(member) })),
        );
        await ctx.reply(successEmbed(`Backed up the roles of ${saved} members.`));
      },
    }),
  },
});
