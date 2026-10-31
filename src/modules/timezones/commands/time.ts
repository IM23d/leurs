import { defineCommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";
import { embed } from "#shared/ui/embeds.ts";

import { getTimezoneSettings } from "../timezones.service.ts";
import { currentTime, SET_ZONE_HINT } from "../timezones.views.ts";

export const timeCommand = defineCommand({
  name: "time",
  description: "Show someone's local time",
  aliases: ["tz"],
  options: { user: opt.user("Whose time").optional() },
  run: async (ctx, { user }) => {
    const target = user ?? ctx.user;
    const self = target.id === ctx.user.id;
    const { zone } = getTimezoneSettings(target.id);
    if (zone === undefined) {
      throw new UserError(
        self
          ? `You haven't set your time zone. ${SET_ZONE_HINT}`
          : `${target.toString()} hasn't set a time zone.`,
      );
    }
    const time = currentTime(zone, getTimezoneSettings(ctx.user.id).use24Hour);
    await ctx.reply(
      embed(
        self ? `Your current time is ${time}.` : `${target.toString()}'s current time is ${time}.`,
      ),
    );
  },
});
