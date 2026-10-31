import { defineCommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";

import { getWeather } from "../weather.service.ts";
import { weatherEmbed } from "../weather.views.ts";

export const weatherCommand = defineCommand({
  name: "weather",
  description: "Show the weather and a 5-day forecast for a place",
  options: { location: opt.string("A city or place, e.g. London").rest() },
  run: async (ctx, { location }) => {
    await ctx.defer();
    await ctx.reply(weatherEmbed(await getWeather(location)));
  },
});
