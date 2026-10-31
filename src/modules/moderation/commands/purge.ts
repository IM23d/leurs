import { PermissionFlagsBits, type Message } from "discord.js";

import type { CommandContext } from "#core/commands/context.ts";
import { defineCommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";
import { chunks } from "#shared/lib/chunks.ts";
import { formatDuration } from "#shared/lib/duration.ts";
import { successEmbed } from "#shared/ui/embeds.ts";

import { asBot } from "../guards.ts";
import { logModAction } from "../mod-log.ts";
import { mentionedUser } from "../options.ts";
import { MAX_PURGE, MAX_TIME_PURGE, parsePurgeTarget, planPurge } from "../purge.service.ts";

const CONFIRMATION_SECONDS = 5;

/**
 * Messages before the prefix command (or the latest, for slash), newest first. Pages back until
 * one is older than `since` or `limit` messages are read. Discord returns 100 per request.
 */
async function recentMessages(ctx: CommandContext, limit: number, since = 0): Promise<Message[]> {
  const collected: Message[] = [];
  let before = ctx.messageId;
  while (collected.length < limit) {
    const page = await ctx.channel.messages.fetch({
      limit: Math.min(MAX_PURGE, limit - collected.length),
      ...(before === undefined ? {} : { before }),
    });
    collected.push(...page.values());
    const oldest = page.last();
    if (page.size < MAX_PURGE || !oldest || oldest.createdTimestamp < since) break;
    before = oldest.id;
  }
  return collected;
}

/** Bulk-deletes in batches of 100, the most Discord accepts at once. */
async function deleteAll(ctx: CommandContext, ids: readonly string[]): Promise<number> {
  let deleted = 0;
  for (const batch of chunks(ids, MAX_PURGE)) {
    deleted += (await asBot("delete messages", () => ctx.channel.bulkDelete(batch, true))).size;
  }
  return deleted;
}

export const purgeCommand = defineCommand({
  name: "purge",
  description: "Delete recent messages in this channel",
  aliases: ["clear", "cclear"],
  permissions: PermissionFlagsBits.ManageMessages,
  options: {
    amount: opt.custom(
      `How many messages (up to ${MAX_PURGE}) or how far back, e.g. 50, 30m, 1d`,
      "number or duration",
      parsePurgeTarget,
    ),
    user: mentionedUser("Only messages from this person").optional(),
    contains: opt.string("Only messages containing this text").rest().optional(),
  },
  run: async (ctx, { amount, user, contains }) => {
    await ctx.defer({ private: true });
    const since = amount.kind === "since" ? Date.now() - amount.ms : undefined;
    const fetched = await (amount.kind === "count"
      ? recentMessages(ctx, MAX_PURGE)
      : recentMessages(ctx, MAX_TIME_PURGE, since));
    const candidates = fetched.map((message) => ({
      id: message.id,
      authorId: message.author.id,
      content: message.content,
      createdAt: message.createdAt,
    }));
    const plan = planPurge(candidates, {
      amount: amount.kind === "count" ? amount.count : undefined,
      since,
      authorId: user?.id,
      contains,
    });
    if (plan.deletable.length === 0 && plan.tooOld === 0) {
      throw new UserError(
        amount.kind === "count"
          ? `No matching messages in the last ${MAX_PURGE}.`
          : `No matching messages in the last ${formatDuration(amount.ms)}.`,
      );
    }
    const deleted = await deleteAll(ctx, plan.deletable);
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
