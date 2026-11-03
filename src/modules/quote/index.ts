import { defineModule } from "#core/module.ts";

import { quoteCommand } from "./commands/quote.ts";
import { quoteContextMenu } from "./context-menus/quote.ts";

export const quoteModule = defineModule({
  name: "quote",
  commands: [quoteCommand],
  contextMenus: [quoteContextMenu],
});
