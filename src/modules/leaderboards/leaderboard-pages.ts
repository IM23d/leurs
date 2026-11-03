import { memberIds } from "#shared/lib/members.ts";
import { embed } from "#shared/ui/embeds.ts";
import { definePaginator, paginate } from "#shared/ui/paginator.ts";

import { boards, isBoardName } from "./boards.ts";

const PAGE_SIZE = 10;
const MEDALS = ["🥇", "🥈", "🥉"];

/** Ranks only members of the current server. Levels and balances are shared across servers. */
export const leaderboardPages = definePaginator({
  id: "leaderboard",
  render: async ({ guild, page, args: [name = "levels"] }) => {
    const board = boards[isBoardName(name) ? name : "levels"];
    const ranked = board.rank([...(await memberIds(guild))]);
    const current = paginate(ranked, page, PAGE_SIZE);
    const lines = current.items.map(([userId, value], index) => {
      const position = current.offset + index;
      const marker = MEDALS[position] ?? `${position + 1}.`;
      return `${marker} <@${userId}> ${value}`;
    });
    return {
      embed: embed(lines.length > 0 ? lines.join("\n") : board.empty)
        .setTitle(board.title)
        .setFooter({ text: `Page ${current.page} of ${current.pageCount}` }),
      pageCount: current.pageCount,
    };
  },
});
