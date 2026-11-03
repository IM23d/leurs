import { defineModule } from "#core/module.ts";

import { balanceCommand } from "./commands/balance.ts";
import { begCommand } from "./commands/beg.ts";
import { gambleCommand } from "./commands/gamble.ts";
import { jobMarket, jobsCommand } from "./commands/jobs.ts";
import { moneyCommand } from "./commands/money.ts";
import { workCommand } from "./commands/work.ts";

export const economyModule = defineModule({
  name: "economy",
  commands: [balanceCommand, begCommand, workCommand, jobsCommand, gambleCommand, moneyCommand],
  components: [jobMarket.component],
});
