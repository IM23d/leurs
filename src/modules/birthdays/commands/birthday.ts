import type { Guild } from "discord.js";

import { defineCommand, subcommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";
import { embed, successEmbed } from "#shared/ui/embeds.ts";
import { definePaginator, paginate } from "#shared/ui/paginator.ts";

import { FORMAT_HINT, parseBirthday } from "../birthday-dates.ts";
import {
  birthdayUserIds,
  getBirthday,
  setBirthday,
  todayFor,
  upcomingBirthday,
  upcomingBirthdays,
} from "../birthdays.service.ts";
import { birthdayText, listLine } from "../birthdays.views.ts";

const PAGE_SIZE = 10;
// Discord returns at most 100 members per lookup by ID.
const MEMBER_BATCH = 100;

async function memberIds(guild: Guild, userIds: readonly string[]): Promise<Set<string>> {
  const batches = Array.from({ length: Math.ceil(userIds.length / MEMBER_BATCH) }, (_, index) =>
    userIds.slice(index * MEMBER_BATCH, (index + 1) * MEMBER_BATCH),
  );
  const found = await Promise.all(batches.map((user) => guild.members.fetch({ user })));
  return new Set(found.flatMap((members) => [...members.keys()]));
}

export const birthdayList = definePaginator({
  id: "birthdays-page",
  render: async ({ guild, page }) => {
    const upcoming = upcomingBirthdays(await memberIds(guild, birthdayUserIds()));
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
