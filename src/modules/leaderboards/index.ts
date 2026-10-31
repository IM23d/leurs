import { defineModule } from "#core/module.ts";

import { leaderboardCommand } from "./commands/leaderboard.ts";
import { leaderboardPages } from "./leaderboard-pages.ts";

export const leaderboardsModule = defineModule({
  name: "leaderboards",
  commands: [leaderboardCommand],
  components: [leaderboardPages.component],
});
