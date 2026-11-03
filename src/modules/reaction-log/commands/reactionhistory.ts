import { PermissionFlagsBits } from "discord.js";

import { defineCommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";
import { parseMessageRef } from "#shared/lib/message-link.ts";

import { historyPages } from "../history-pages.ts";

export const reactionHistoryCommand = defineCommand({
  name: "reactionhistory",
  description: "See who added and removed which reactions on a message",
  aliases: ["rh"],
  permissions: PermissionFlagsBits.ManageMessages,
  options: {
    message: opt
      .custom(
        "A message link or ID. With the prefix you can reply to the message instead",
        "message link",
        parseMessageRef,
      )
      .optional(),
  },
  run: async (ctx, { message }) => {
    const messageId = message?.messageId ?? (await ctx.referencedMessage())?.id;
    if (messageId === undefined) {
      throw new UserError("Give a message link, or reply to the message.");
    }
    await historyPages.reply(ctx, { args: [messageId] });
  },
});
