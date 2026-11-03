import { defineModule } from "#core/module.ts";

import { clownboardCommand } from "./commands/clownboard.ts";
import { clownMenu } from "./context-menus/clown.ts";
import { clownVoteAddedEvent, clownVoteRemovedEvent } from "./events/clown-reactions.ts";

export const clownboardModule = defineModule({
  name: "clownboard",
  commands: [clownboardCommand],
  contextMenus: [clownMenu],
  events: [clownVoteAddedEvent, clownVoteRemovedEvent],
});
