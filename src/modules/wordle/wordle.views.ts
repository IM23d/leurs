import type { EmbedBuilder, User } from "discord.js";

import { embed } from "#shared/ui/embeds.ts";

import type { GroupStats, PlayerStats } from "./wordle.service.ts";

const BAR_WIDTH = 12;
const LABELS = ["1", "2", "3", "4", "5", "6", "X"];

const percent = (part: number, whole: number) =>
  whole === 0 ? "0%" : `${Math.round((part / whole) * 100)}%`;

const average = (value: number | undefined) => (value === undefined ? "–" : value.toFixed(2));

/** A text bar chart of guesses, scaled to the most common score. */
function distribution(counts: readonly number[]): string {
  const most = Math.max(1, ...counts);
  const rows = counts.map((count, index) => {
    const bar = "█".repeat(Math.round((count / most) * BAR_WIDTH));
    return `${LABELS[index] ?? "?"} ${bar.padEnd(BAR_WIDTH, " ")} ${count}`;
  });
  return `\`\`\`\n${rows.join("\n")}\n\`\`\``;
}

export function playerEmbed(user: User, stats: PlayerStats | undefined): EmbedBuilder {
  if (!stats) return embed(`${user.toString()} has no Wordle results here yet.`);
  return embed()
    .setTitle(`Wordle stats for ${user.displayName}`)
    .addFields(
      { name: "Played", value: String(stats.played), inline: true },
      {
        name: "Solved",
        value: `${stats.solved} (${percent(stats.solved, stats.played)})`,
        inline: true,
      },
      { name: "Average guesses", value: average(stats.average), inline: true },
      { name: "Crowns", value: String(stats.crowns), inline: true },
      { name: "Current streak", value: `${stats.currentStreak} days`, inline: true },
      { name: "Best streak", value: `${stats.bestStreak} days`, inline: true },
      { name: "Guesses", value: distribution(stats.distribution) },
    );
}

/** Players ranked by average guesses. Players with no solved game come last. */
export function leaderboardEmbed(group: GroupStats): EmbedBuilder {
  const ranked = group.players.toSorted(
    (a, b) => (a.average ?? 7) - (b.average ?? 7) || b.solved - a.solved,
  );
  const lines = ranked.map(
    (player, index) =>
      `${index + 1}. <@${player.userId}> **${average(player.average)}** avg · ${player.solved}/${player.played} solved · ${player.crowns} crowns`,
  );
  return embed(lines.length > 0 ? lines.join("\n") : "No Wordle results yet.")
    .setTitle("Wordle leaderboard")
    .setFooter({
      text: `${group.days} days · ${group.games} games · ${percent(group.solved, group.games)} solved`,
    });
}
