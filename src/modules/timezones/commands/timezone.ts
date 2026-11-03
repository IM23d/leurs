import { defineCommand, subcommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";
import { successEmbed } from "#shared/ui/embeds.ts";

import { getTimezoneSettings, setUse24Hour, setZone } from "../timezones.service.ts";
import { currentTime, SET_ZONE_HINT } from "../timezones.views.ts";
import { findTimezone, suggestZones } from "../zones.ts";

const FORMATS = [
  { name: "12-hour", value: "12" },
  { name: "24-hour", value: "24" },
];

export const timezoneCommand = defineCommand({
  name: "timezone",
  description: "Set your time zone and time format",
  subcommands: {
    set: subcommand({
      description: "Set your time zone",
      aliases: ["tz set"],
      options: {
        zone: opt
          .string("A city, abbreviation or IANA zone, e.g. Berlin, CET or Europe/Zurich")
          .rest()
          .autocomplete((query) => suggestZones(query)),
      },
      run: async (ctx, { zone: query }) => {
        const zone = findTimezone(query);
        if (zone === undefined) {
          throw new UserError(
            "I don't know that time zone. Try a city such as Berlin or a code such as CET.",
          );
        }
        setZone(ctx.user.id, zone);
        const { use24Hour } = getTimezoneSettings(ctx.user.id);
        await ctx.reply(
          successEmbed(`Time zone set. Your current time is ${currentTime(zone, use24Hour)}.`),
        );
      },
    }),
    format: subcommand({
      description: "Show times in 12 or 24 hour format",
      aliases: ["tz format"],
      options: { format: opt.string("Leave empty to switch").choices(FORMATS).optional() },
      run: async (ctx, { format }) => {
        const before = getTimezoneSettings(ctx.user.id);
        const use24Hour = format === undefined ? !before.use24Hour : format === "24";
        setUse24Hour(ctx.user.id, use24Hour);
        const time =
          before.zone === undefined
            ? SET_ZONE_HINT
            : `Your current time is ${currentTime(before.zone, use24Hour)}.`;
        await ctx.reply(
          successEmbed(`Times now show in **${use24Hour ? "24" : "12"}-hour** format.\n${time}`),
        );
      },
    }),
  },
});
