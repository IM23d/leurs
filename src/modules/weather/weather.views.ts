import type { EmbedBuilder } from "discord.js";

import { embed } from "#shared/ui/embeds.ts";

import type { WeatherReport } from "./weather.service.ts";

export function weatherEmbed(report: WeatherReport): EmbedBuilder {
  const forecast = report.days
    .map(({ day, emoji, min, max }) => `${day}: ${emoji} ${min}°C - ${max}°C`)
    .join("\n");
  const built = embed(`**Current conditions:** ${report.emoji} ${report.temperature}°C`)
    .setTitle(`Weather for ${report.location}`)
    .addFields(
      { name: "Feels like", value: `**${report.feelsLike}°C**`, inline: true },
      {
        name: "Today's range",
        value: `🔽 ${report.todayMin}°C / 🔼 ${report.todayMax}°C`,
        inline: true,
      },
      {
        name: "Humidity and wind",
        value: `💧 ${report.humidity}% | 💨 ${report.windSpeed} km/h`,
        inline: true,
      },
    )
    .setTimestamp();
  return forecast === "" ? built : built.addFields({ name: "5-day forecast", value: forecast });
}
