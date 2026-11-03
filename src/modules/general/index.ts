import { defineModule } from "#core/module.ts";

import { aboutCommand } from "./commands/about.ts";
import { helpCommand } from "./commands/help.ts";

export const generalModule = defineModule({
  name: "general",
  commands: [helpCommand, aboutCommand],
});
