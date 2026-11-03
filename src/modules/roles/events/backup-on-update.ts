import { defineEvent } from "#core/events.ts";

import { backupRoleIds } from "../role-access.ts";
import { saveBackup } from "../role-backups.service.ts";

export const backupOnUpdateEvent = defineEvent({
  name: "guildMemberUpdate",
  run: (before, after) => {
    const unchanged = !before.partial && before.roles.cache.equals(after.roles.cache);
    if (!after.user.bot && !unchanged) {
      saveBackup(after.guild.id, { userId: after.id, roleIds: backupRoleIds(after) });
    }
    return Promise.resolve();
  },
});
