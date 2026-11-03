import { messageLink } from "#shared/lib/message-link.ts";
import { embed } from "#shared/ui/embeds.ts";
import { definePaginator } from "#shared/ui/paginator.ts";

import { reactionHistory, RETENTION_MS } from "./reaction-log.service.ts";
import { historyLine } from "./reaction-log.views.ts";

const PAGE_SIZE = 15;
const RETENTION_DAYS = RETENTION_MS / 86_400_000;

/** A message's reactions over time. Argument: the message ID. */
export const historyPages = definePaginator({
  id: "reaction-history",
  render: ({ guild, page, args: [messageId = ""] }) => {
    const { total } = reactionHistory(guild.id, messageId, 0, 0);
    const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
    const current = Math.min(Math.max(1, page), pageCount);
    const { events } = reactionHistory(guild.id, messageId, (current - 1) * PAGE_SIZE, PAGE_SIZE);
    const first = events[0];
    const link = first
      ? `[Jump to the message](${messageLink(guild.id, first.channelId, messageId)})\n\n`
      : "";
    return {
      embed: embed(
        events.length > 0
          ? link + events.map(historyLine).join("\n")
          : `No reaction changes recorded for this message in the last ${RETENTION_DAYS} days.`,
      )
        .setTitle("Reaction history")
        .setFooter({ text: `Page ${current} of ${pageCount} · kept for ${RETENTION_DAYS} days` }),
      pageCount,
    };
  },
});
