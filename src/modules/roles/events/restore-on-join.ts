import type { Role } from "discord.js";

import { defineEvent } from "#core/events.ts";
import { successEmbed } from "#shared/ui/embeds.ts";

import { getBackup } from "../role-backups.service.ts";

export const restoreOnJoinEvent = defineEvent({
  name: "guildMemberAdd",
  run: async (member) => {
    if (member.user.bot) return;
    const { guild } = member;
    // `editable` leaves out managed roles and roles at or above the bot's highest role.
    const roles = getBackup(guild.id, member.id)
      .map((id) => guild.roles.cache.get(id))
      .filter((role): role is Role => role !== undefined && role.id !== guild.id && role.editable);
    if (roles.length === 0) return;
    await member.roles.add(roles, "Restoring saved roles");
    const notice = successEmbed(
      `Gave ${member.toString()} their roles back: ${roles.map(String).join(", ")}`,
    ).setTitle("Roles restored");
    await guild.systemChannel?.send({ embeds: [notice] }).catch(() => undefined);
  },
});
