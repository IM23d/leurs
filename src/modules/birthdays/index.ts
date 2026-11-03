import { defineModule } from "#core/module.ts";

import { birthdayCommand, birthdayList } from "./commands/birthday.ts";

export const birthdaysModule = defineModule({
  name: "birthdays",
  commands: [birthdayCommand],
  components: [birthdayList.component],
});
