import { defineModule } from "#core/module.ts";

import { weatherCommand } from "./commands/weather.ts";

export const weatherModule = defineModule({
  name: "weather",
  commands: [weatherCommand],
});
