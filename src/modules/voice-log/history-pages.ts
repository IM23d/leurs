import { embed } from "#shared/ui/embeds.ts";
import { definePaginator } from "#shared/ui/paginator.ts";

import { history } from "./voice-log.service.ts";
import { historyLine } from "./voice-log.views.ts";

const PAGE_SIZE = 10;
/** Placeholder in the button ID when no channel or user filter is set. */
export const ANY = "-";

const filter = (value: string | undefined) =>
  value === undefined || value === ANY ? undefined : value;

/** Past and current stays, newest first. Arguments: channel ID and user ID, or ANY. */
export const historyPages = definePaginator({
  id: "voice-history",
  render: ({ guild, page, args: [channelId, userId] }) => {
    const query = { guildId: guild.id, channelId: filter(channelId), userId: filter(userId) };
    const { total } = history(query, 0, 0);
    const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
    const current = Math.min(Math.max(1, page), pageCount);
    const { stays } = history(query, (current - 1) * PAGE_SIZE, PAGE_SIZE);
    const now = new Date();
    return {
      embed: embed(
        stays.length > 0
          ? stays.map((stay) => historyLine(stay, now)).join("\n\n")
          : "No voice activity recorded for this filter.",
      )
        .setTitle("Voice history")
        .setFooter({ text: `Page ${current} of ${pageCount} · kept for 30 days` }),
      pageCount,
    };
  },
});
