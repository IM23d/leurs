import { defineCommand, subcommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";
import { memberIds } from "#shared/lib/members.ts";
import { embed, successEmbed } from "#shared/ui/embeds.ts";
import { definePaginator, paginate } from "#shared/ui/paginator.ts";

import { FORMAT_HINT, parseBirthday } from "../birthday-dates.ts";
import {
  getBirthday,
  setBirthday,
  todayFor,
  upcomingBirthday,
  upcomingBirthdays,
} from "../birthdays.service.ts";
import { birthdayText, listLine } from "../birthdays.views.ts";

const PAGE_SIZE = 10;

export const birthdayList = definePaginator({
  id: "birthdays-page",
  render: async ({ guild, page }) => {
    const upcoming = upcomingBirthdays(await memberIds(guild));
    const current = paginate(upcoming, page, PAGE_SIZE);
    const text =
      current.items.length > 0
        ? current.items.map(listLine).join("\n")
        : "No one here has set a birthday yet.";
    return {
      embed: embed(text)
        .setTitle("Upcoming birthdays")
        .setFooter({ text: `Page ${current.page} of ${current.pageCount}` }),
      pageCount: current.pageCount,
    };
  },
});

export const birthdayCommand = defineCommand({
  name: "birthday",
  description: "Show, set and list birthdays",
  aliases: ["bday"],
  defaultSubcommand: "show",
  subcommands: {
    show: subcommand({
      description: "Show someone's birthday",
      options: { user: opt.user("Whose birthday").optional() },
      run: async (ctx, { user }) => {
        const target = user ?? ctx.user;
        const self = target.id === ctx.user.id;
        const birthday = getBirthday(target.id);
        if (!birthday) {
          throw new UserError(
            self
              ? "You haven't set your birthday. Use `/birthday set` with a date such as 31-12-2000."
              : `${target.toString()} hasn't set their birthday.`,
          );
        }
        const upcoming = upcomingBirthday(target.id, birthday);
        await ctx.reply(embed(birthdayText(upcoming, self ? undefined : target.toString())));
      },
    }),
    set: subcommand({
      description: "Set your birthday",
      aliases: ["bday set"],
      options: { date: opt.string(`Your birthday. ${FORMAT_HINT}`) },
      run: async (ctx, { date }) => {
        const birthday = parseBirthday(date, todayFor(ctx.user.id));
        setBirthday(ctx.user.id, birthday);
        await ctx.reply(
          successEmbed(birthdayText(upcomingBirthday(ctx.user.id, birthday), undefined)),
        );
      },
    }),
    list: subcommand({
      description: "List upcoming birthdays in this server",
      aliases: ["bday list"],
      run: async (ctx) => {
        await birthdayList.reply(ctx);
      },
    }),
  },
});
