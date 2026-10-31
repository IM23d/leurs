import { PermissionFlagsBits, type Message, type User } from "discord.js";

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
import {
  MAX_PURGE,
  parsePurgeTarget,
  planPurge,
  readLeadingWords,
  purgeScope,
  type PurgeTarget,
} from "../purge.service.ts";

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

interface PurgeValues {
  readonly amount: PurgeTarget | undefined;
  readonly user: User | undefined;
  readonly contains: string | undefined;
  readonly duplicates: boolean | undefined;
}

const toCandidate = (message: Message) => ({
  id: message.id,
  authorId: message.author.id,
  content: message.content,
  createdAt: message.createdAt,
});

async function report(
  ctx: CommandContext,
  {
    deleted,
    tooOld,
    user,
    contains,
    duplicates,
  }: { deleted: number; tooOld: number } & Omit<PurgeValues, "amount">,
): Promise<void> {
  const skipped = tooOld === 0 ? "" : ` Skipped ${tooOld} older than 14 days.`;
  await ctx.reply({
    embeds: [successEmbed(`Deleted ${deleted} message${deleted === 1 ? "" : "s"}.${skipped}`)],
    private: true,
    deleteAfter: CONFIRMATION_SECONDS,
  });
  const filters = [
    duplicates && "duplicates only",
    user && `from ${user.toString()}`,
    contains && `containing "${contains}"`,
  ]
    .filter(Boolean)
    .join(", ");
  await logModAction(ctx.guild, {
    title: "Purge",
    moderator: ctx.user,
    details: `Deleted ${deleted} in ${ctx.channel.toString()}${filters ? `, ${filters}` : ""}.`,
  });
}

export const purgeCommand = defineCommand({
  name: "purge",
  description: "Delete recent messages in this channel",
  aliases: ["clear", "cclear"],
  permissions: PermissionFlagsBits.ManageMessages,
  options: {
    amount: opt
      .custom(
        `How many messages (up to ${MAX_PURGE}) or how far back, e.g. 50, 30m, 1d`,
        "number or duration",
        parsePurgeTarget,
      )
      .optional(),
    user: mentionedUser("Only messages from this person").optional(),
    duplicates: opt
      .boolean("Only messages that repeat an earlier one, keeping the first")
      .optional(),
    contains: opt.string("Only messages containing this text").rest().optional(),
  },
  run: async (ctx, values) => {
    const { amount, user, contains, duplicates } = readLeadingWords(values);
    if (amount === undefined && user === undefined && !duplicates) {
      throw new UserError("Give an amount, a time span like `30m`, a user, or `duplicates`.");
    }
    await ctx.defer({ private: true });
    // With duplicates, a count is the number of messages to check, so no deeper search.
    const filtered = !duplicates && (user !== undefined || contains !== undefined);
    const scope = purgeScope(amount, filtered, Date.now());
    const fetched = await recentMessages(ctx, scope.scanLimit, scope.since);
    const plan = planPurge(fetched.map(toCandidate), {
      amount: scope.count,
      since: scope.since,
      authorId: user?.id,
      contains,
      duplicates,
    });
    if (plan.deletable.length === 0 && plan.tooOld === 0) {
      throw new UserError(
        amount?.kind === "since"
          ? `No matching messages in the last ${formatDuration(amount.ms)}.`
          : "No matching messages found.",
      );
    }
    const deleted = await deleteAll(ctx, plan.deletable);
    // The prefix command goes too, so only the short confirmation is left, and then nothing.
    if (ctx.messageId !== undefined) {
      await ctx.channel.messages.delete(ctx.messageId).catch(() => undefined);
    }
    await report(ctx, { deleted, tooOld: plan.tooOld, user, contains, duplicates });
  },
});
