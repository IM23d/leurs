import { defineModule } from "#core/module.ts";

import { aiCommand } from "./commands/ai.ts";
import { translateMenu } from "./commands/translate-menu.ts";
import { translateCommand } from "./commands/translate.ts";
import { usageCommand } from "./commands/usage.ts";

export const aiModule = defineModule({
  name: "ai",
  commands: [aiCommand, translateCommand, usageCommand],
  contextMenus: [translateMenu],
});
