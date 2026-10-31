import { defineModule } from "#core/module.ts";

import { reactionHistoryCommand } from "./commands/reactionhistory.ts";
import { reactionSnipeCommand } from "./commands/reactionsnipe.ts";
import { logReactionAdd, logReactionRemove } from "./events/log-reactions.ts";
import { pruneReactionsEvent } from "./events/prune-reactions.ts";
import { historyPages } from "./history-pages.ts";

export const reactionLogModule = defineModule({
  name: "reaction log",
  commands: [reactionHistoryCommand, reactionSnipeCommand],
  components: [historyPages.component],
  events: [logReactionAdd, logReactionRemove, pruneReactionsEvent],
});
