import { defineModule } from "#core/module.ts";

import { reminderList, remindCommand } from "./commands/remind.ts";
import { reminderTask } from "./tasks/deliver-reminder.ts";

export const remindersModule = defineModule({
  name: "reminders",
  commands: [remindCommand],
  components: [reminderList.component],
  tasks: [reminderTask],
});
