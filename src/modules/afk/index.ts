import { defineModule } from "#core/module.ts";

import { afkCommand } from "./commands/afk.ts";
import { afkMessages } from "./events/afk-messages.ts";

export const afkModule = defineModule({
  name: "afk",
  commands: [afkCommand],
  events: [afkMessages],
});
