import { ActionRowBuilder, ButtonBuilder, ButtonStyle } from "discord.js";

import { customId, defineComponent } from "#core/components.ts";

import { isSortName, SORTS, type SortName } from "../wordle-sort.ts";
import { groupStats } from "../wordle.service.ts";
import { leaderboardEmbed } from "../wordle.views.ts";

/** The leaderboard with one button per sort. The current sort is highlighted. */
export function leaderboardMessage(guildId: string, sort: SortName) {
  const buttons = (Object.keys(SORTS) as SortName[]).map((name) =>
    new ButtonBuilder()
      .setCustomId(customId(leaderboardSort, name))
      .setLabel(SORTS[name].label)
      .setStyle(name === sort ? ButtonStyle.Primary : ButtonStyle.Secondary)
      .setDisabled(name === sort),
  );
  return {
    embeds: [leaderboardEmbed(groupStats(guildId), sort)],
    components: [new ActionRowBuilder<ButtonBuilder>().addComponents(buttons)],
  };
}

/** Re-sorts the leaderboard in place. Anyone may switch the sort. */
export const leaderboardSort = defineComponent({
  id: "wordle-sort",
  run: async (interaction, [sort = "crowns"]) => {
    if (!interaction.isButton()) return;
    await interaction.update(
      leaderboardMessage(interaction.guildId, isSortName(sort) ? sort : "crowns"),
    );
  },
});
