import { defineEvent } from "#core/events.ts";

import { backupRoleIds } from "../role-access.ts";
import { saveBackup } from "../role-backups.service.ts";

export const backupOnLeaveEvent = defineEvent({
  name: "guildMemberRemove",
  run: (member) => {
    // An uncached member's roles are unknown, so the backup from their last role change stays.
    if (!member.partial && !member.user.bot) {
      saveBackup(member.guild.id, { userId: member.id, roleIds: backupRoleIds(member) });
    }
    return Promise.resolve();
  },
});
