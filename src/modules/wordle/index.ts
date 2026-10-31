import { defineModule } from "#core/module.ts";

import { wordleCommand } from "./commands/wordle.ts";
import { leaderboardSort } from "./components/leaderboard-sort.ts";
import { recordResultsEvent } from "./events/record-results.ts";

export const wordleModule = defineModule({
  name: "wordle",
  commands: [wordleCommand],
  components: [leaderboardSort],
  events: [recordResultsEvent],
});
