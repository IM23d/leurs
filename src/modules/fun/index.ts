import { defineModule } from "#core/module.ts";

import { fortuneCommand } from "./commands/fortune.ts";
import { funCommand } from "./commands/fun.ts";

export const funModule = defineModule({
  name: "fun",
  commands: [fortuneCommand, funCommand],
});
