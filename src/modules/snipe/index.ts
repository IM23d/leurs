import { defineModule } from "#core/module.ts";

import { snipeCommand } from "./commands/snipe.ts";
import { rememberDeleted } from "./events/remember-deleted.ts";

export const snipeModule = defineModule({
  name: "snipe",
  commands: [snipeCommand],
  events: [rememberDeleted],
});
