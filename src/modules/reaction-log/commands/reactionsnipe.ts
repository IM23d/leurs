import { defineCommand } from "#core/commands/define.ts";
import { UserError } from "#core/errors.ts";
import { messageLink } from "#shared/lib/message-link.ts";
import { embed } from "#shared/ui/embeds.ts";

import { latestRemoval } from "../reaction-log.service.ts";
import { removalLine } from "../reaction-log.views.ts";

/** Same window as message snipe. */
const SNIPE_WINDOW_MS = 2 * 3_600_000;

export const reactionSnipeCommand = defineCommand({
  name: "reactionsnipe",
  description: "Show the last reaction someone removed in this channel",
  aliases: ["rs"],
  run: async (ctx) => {
    const event = latestRemoval(ctx.channel.id, new Date(Date.now() - SNIPE_WINDOW_MS));
    if (!event) throw new UserError("No reaction was removed here in the last 2 hours.");
    const link = messageLink(event.guildId, event.channelId, event.messageId);
    await ctx.reply(embed(removalLine(event, link)));
  },
});
