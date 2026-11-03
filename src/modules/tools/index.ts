import { defineModule } from "#core/module.ts";

import { autoReactList, autoreactCommand } from "./commands/autoreact.ts";
import { embedCommand } from "./commands/embed.ts";
import { embedEditor } from "./components/embed-editor.ts";
import { autoReactEvent } from "./events/auto-react.ts";

export const toolsModule = defineModule({
  name: "tools",
  commands: [autoreactCommand, embedCommand],
  components: [autoReactList.component, embedEditor],
  events: [autoReactEvent],
});
