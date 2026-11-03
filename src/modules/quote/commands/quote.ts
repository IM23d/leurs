import { defineCommand } from "#core/commands/define.ts";
import { UserError } from "#core/errors.ts";

import { quoteAttachment } from "../quote.views.ts";

export const quoteCommand = defineCommand({
  name: "quote",
  description: "Turn a message into a quote image",
  run: async (ctx) => {
    if (ctx.source === "slash") {
      throw new UserError("Right-click a message and pick Apps > Quote.");
    }
    const message = await ctx.referencedMessage();
    if (!message) throw new UserError("Reply to a message to quote it.");
    await ctx.defer();
    await ctx.reply({ files: [await quoteAttachment(message)] });
  },
});
