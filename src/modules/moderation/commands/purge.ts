import { PermissionFlagsBits, type Message } from "discord.js";

import type { CommandContext } from "#core/commands/context.ts";
import { defineCommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";
import { successEmbed } from "#shared/ui/embeds.ts";

import { asBot } from "../guards.ts";
import { logModAction } from "../mod-log.ts";
import { mentionedUser } from "../options.ts";
import { MAX_PURGE, planPurge } from "../purge.service.ts";

const CONFIRMATION_SECONDS = 5;

/** The latest messages, newest first, without the prefix command that started the purge. */
async function recentMessages(ctx: CommandContext): Promise<Message[]> {
  const messages = await ctx.channel.messages.fetch({ limit: MAX_PURGE + 1 });
  return [...messages.values()]
    .filter((message) => message.id !== ctx.messageId)
    .slice(0, MAX_PURGE);
}

export const purgeCommand = defineCommand({
  name: "purge",
  description: "Delete recent messages in this channel",
  aliases: ["clear", "cclear"],
  permissions: PermissionFlagsBits.ManageMessages,
  options: {
    amount: opt.integer("How many messages to delete").min(1).max(MAX_PURGE),
    user: mentionedUser("Only messages from this person").optional(),
    contains: opt.string("Only messages containing this text").rest().optional(),
  },
  run: async (ctx, { amount, user, contains }) => {
    await ctx.defer({ private: true });
    const candidates = (await recentMessages(ctx)).map((message) => ({
      id: message.id,
      authorId: message.author.id,
      content: message.content,
      createdAt: message.createdAt,
    }));
    const plan = planPurge(candidates, { amount, authorId: user?.id, contains });
    if (plan.deletable.length === 0 && plan.tooOld === 0) {
      throw new UserError(`No matching messages in the last ${MAX_PURGE}.`);
    }
    const deleted =
      plan.deletable.length === 0
        ? 0
        : (await asBot("delete messages", () => ctx.channel.bulkDelete(plan.deletable, true))).size;
    // The prefix command goes too, so only the short confirmation is left, and then nothing.
    if (ctx.messageId !== undefined) {
      await ctx.channel.messages.delete(ctx.messageId).catch(() => undefined);
    }
    const skipped = plan.tooOld === 0 ? "" : ` Skipped ${plan.tooOld} older than 14 days.`;
    await ctx.reply({
      embeds: [successEmbed(`Deleted ${deleted} message${deleted === 1 ? "" : "s"}.${skipped}`)],
      private: true,
      deleteAfter: CONFIRMATION_SECONDS,
    });
    const filters = [user && `from ${user.toString()}`, contains && `containing "${contains}"`]
      .filter(Boolean)
      .join(", ");
    await logModAction(ctx.guild, {
      title: "Purge",
      moderator: ctx.user,
      details: `Deleted ${deleted} in ${ctx.channel.toString()}${filters ? `, ${filters}` : ""}.`,
    });
  },
});
