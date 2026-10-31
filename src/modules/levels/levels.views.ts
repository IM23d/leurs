import type { EmbedBuilder, User } from "discord.js";

import { embed, successEmbed } from "#shared/ui/embeds.ts";

import { levelProgress } from "./levels.math.ts";
import type { LevelStats } from "./levels.service.ts";

const BAR_LENGTH = 10;

const count = (value: number): string => value.toLocaleString("en-US");

const progressBar = (percent: number): string => {
  const filled = Math.floor(percent / (100 / BAR_LENGTH));
  return "🟦".repeat(filled) + "⬜".repeat(BAR_LENGTH - filled);
};

const voiceTime = (seconds: number): string =>
  `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;

export function rankEmbed(user: User, name: string, stats: LevelStats): EmbedBuilder {
  const progress = levelProgress(stats.xp);
  return embed()
    .setTitle(name)
    .setThumbnail(user.displayAvatarURL())
    .addFields(
      { name: "Level", value: `**${progress.level}**`, inline: true },
      { name: "Total XP", value: `**${count(stats.xp)}**`, inline: true },
      { name: "Messages", value: `**${count(stats.messages)}**`, inline: true },
      {
        name: `Progress to level ${progress.level + 1}`,
        value: `${progressBar(progress.percent)} **${progress.percent}%**\n${count(progress.current)}/${count(progress.needed)} XP`,
      },
      { name: "Time in voice", value: `**${voiceTime(stats.voiceSeconds)}**`, inline: true },
    );
}

export const levelUpEmbed = (user: User, level: number): EmbedBuilder =>
  embed(`Congratulations ${user.toString()}! You reached **level ${level}**.`)
    .setTitle("Level up 🎉")
    .setThumbnail(user.displayAvatarURL());

export const setMessagesEmbed = (user: User, stats: LevelStats): EmbedBuilder =>
  successEmbed(
    [
      `Updated ${user.toString()}:`,
      `Messages: **${count(stats.messages)}**`,
      `XP: **${count(stats.xp)}**`,
      `Level: **${count(stats.level)}**`,
    ].join("\n"),
  );
