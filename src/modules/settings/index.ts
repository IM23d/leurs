import { defineModule } from "#core/module.ts";

import { prefixCommand } from "./commands/prefix.ts";
import { settingsCommand } from "./commands/settings.ts";

export const settingsModule = defineModule({
  name: "settings",
  commands: [prefixCommand, settingsCommand],
});
