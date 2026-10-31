import { defineModule } from "#core/module.ts";

import { banCommand } from "./commands/ban.ts";
import { blockedTermsPaginator, blocktermCommand } from "./commands/blockterm.ts";
import { jailCommand } from "./commands/jail.ts";
import { kickCommand } from "./commands/kick.ts";
import { modlogCommand, modlogPaginator } from "./commands/modlog.ts";
import { muteCommand } from "./commands/mute.ts";
import { nickCommand } from "./commands/nick.ts";
import { purgeCommand } from "./commands/purge.ts";
import { unjailCommand } from "./commands/unjail.ts";
import { unmuteCommand } from "./commands/unmute.ts";
import { warnCommand } from "./commands/warn.ts";
import { blockedTermsEvent } from "./events/blocked-terms.ts";
import { releaseJailTask } from "./tasks/release-jail.ts";
import { unbanTask } from "./tasks/unban.ts";

export const moderationModule = defineModule({
  name: "moderation",
  commands: [
    warnCommand,
    modlogCommand,
    banCommand,
    kickCommand,
    muteCommand,
    unmuteCommand,
    jailCommand,
    unjailCommand,
    purgeCommand,
    nickCommand,
    blocktermCommand,
  ],
  components: [modlogPaginator.component, blockedTermsPaginator.component],
  events: [blockedTermsEvent],
  tasks: [releaseJailTask, unbanTask],
});
