import { defineModule } from "#core/module.ts";

import { wordleCommand } from "./commands/wordle.ts";
import { recordResultsEvent } from "./events/record-results.ts";

export const wordleModule = defineModule({
  name: "wordle",
  commands: [wordleCommand],
  events: [recordResultsEvent],
});
