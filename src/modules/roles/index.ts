import { defineModule } from "#core/module.ts";

import { reactionRoleList, reactionroleCommand } from "./commands/reactionrole.ts";
import { rolebackupCommand } from "./commands/rolebackup.ts";
import { temproleCommand } from "./commands/temprole.ts";
import { backupOnLeaveEvent } from "./events/backup-on-leave.ts";
import { backupOnUpdateEvent } from "./events/backup-on-update.ts";
import { reactionRoleAddEvent } from "./events/reaction-role-add.ts";
import { reactionRoleRemoveEvent } from "./events/reaction-role-remove.ts";
import { restoreOnJoinEvent } from "./events/restore-on-join.ts";
import { expireTempRole } from "./tasks/expire-temp-role.ts";

export const rolesModule = defineModule({
  name: "roles",
  commands: [temproleCommand, rolebackupCommand, reactionroleCommand],
  components: [reactionRoleList.component],
  events: [
    backupOnUpdateEvent,
    backupOnLeaveEvent,
    restoreOnJoinEvent,
    reactionRoleAddEvent,
    reactionRoleRemoveEvent,
  ],
  tasks: [expireTempRole],
});
