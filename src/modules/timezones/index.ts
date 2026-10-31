import { defineModule } from "#core/module.ts";

import { timeCommand } from "./commands/time.ts";
import { timezoneCommand } from "./commands/timezone.ts";

export const timezonesModule = defineModule({
  name: "timezones",
  commands: [timeCommand, timezoneCommand],
});
