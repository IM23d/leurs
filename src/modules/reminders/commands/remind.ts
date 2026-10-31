import { time, TimestampStyles } from "discord.js";

import { defineCommand, subcommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";
import { zoneFor } from "#modules/timezones/api.ts";
import { truncate } from "#shared/lib/text.ts";
import { embed, successEmbed } from "#shared/ui/embeds.ts";
import { definePaginator, paginate } from "#shared/ui/paginator.ts";

import { cancelReminder, DEFAULT_REASON, remindersOf, setReminder } from "../reminders.service.ts";
import { parseWhen, WHEN_FORMATS } from "../when.ts";

const PAGE_SIZE = 10;
const MAX_REASON_LENGTH = 1000;
// Ten full-length reasons would pass the 4096-character embed description limit.
const LISTED_REASON_LENGTH = 200;

const timestamp = (date: Date, style: "F" | "R") =>
  time(date, style === "F" ? TimestampStyles.FullDateShortTime : TimestampStyles.RelativeTime);

export const reminderList = definePaginator({
  id: "reminders-page",
  render: ({ page, args: [userId = ""] }) => {
    const reminders = remindersOf(userId);
    const current = paginate(reminders, page, PAGE_SIZE);
    const lines = current.items.map(
      ({ id, runAt, reason }) =>
        `**#${id}** ${timestamp(runAt, "F")} (${timestamp(runAt, "R")})\n${truncate(reason, LISTED_REASON_LENGTH)}`,
    );
    return {
      embed: embed(lines.length > 0 ? lines.join("\n\n") : "You don't have any reminders.")
        .setTitle("Your reminders")
        .setFooter({ text: `Page ${current.page} of ${current.pageCount}` }),
      pageCount: current.pageCount,
    };
  },
});

export const remindCommand = defineCommand({
  name: "remind",
  description: "Set, list and cancel reminders",
  defaultSubcommand: "set",
  subcommands: {
    set: subcommand({
      description: "Remind yourself of something later",
      aliases: ["remindme", "rm"],
      options: {
        when: opt.string("When, e.g. 15m, 20:00, 8pm, tomorrow or 15.05"),
        what: opt.string("What to remind you of").max(MAX_REASON_LENGTH).rest().optional(),
      },
      run: async (ctx, { when, what }) => {
        const now = new Date();
        const runAt = parseWhen(when, now, zoneFor(ctx.user.id));
        if (runAt === undefined) {
          throw new UserError(
            `I couldn't read that time. Use one of these:\n${WHEN_FORMATS.map((format) => `- ${format}`).join("\n")}\nTimes and dates use your time zone from \`/timezone set\`, or UTC.`,
          );
        }
        const reminder = setReminder(
          { userId: ctx.user.id, channelId: ctx.channel.id, reason: what ?? DEFAULT_REASON, runAt },
          now,
        );
        await ctx.reply(
          successEmbed(
            `I'll remind you ${timestamp(runAt, "R")}.\n**Reason:** ${reminder.reason}\n**Time:** ${timestamp(runAt, "F")}`,
          )
            .setTitle("Reminder set")
            .setFooter({ text: `ID ${reminder.id}` }),
        );
      },
    }),
    list: subcommand({
      description: "List your reminders",
      aliases: ["reminders"],
      run: async (ctx) => {
        // The list shows reminders set in other servers too, so only the owner sees it.
        await reminderList.reply(ctx, { args: [ctx.user.id], private: true });
      },
    }),
    cancel: subcommand({
      description: "Cancel a reminder",
      options: { id: opt.integer("The reminder's ID from /remind list").min(1) },
      run: async (ctx, { id }) => {
        if (!cancelReminder(ctx.user.id, id)) {
          throw new UserError(`You don't have a reminder #${id}.`);
        }
        await ctx.reply(successEmbed(`Reminder #${id} cancelled.`));
      },
    }),
  },
});
