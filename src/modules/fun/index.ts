import { defineModule } from "#core/module.ts";

import { fortuneCommand } from "./commands/fortune.ts";

export const funModule = defineModule({
  name: "fun",
  commands: [fortuneCommand],
});
