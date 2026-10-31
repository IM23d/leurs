import { defineModule } from "#core/module.ts";

import { clownboardCommand } from "./commands/clownboard.ts";
import { clownAddedEvent, clownRemovedEvent } from "./events/clown-reactions.ts";

export const clownboardModule = defineModule({
  name: "clownboard",
  commands: [clownboardCommand],
  events: [clownAddedEvent, clownRemovedEvent],
});
