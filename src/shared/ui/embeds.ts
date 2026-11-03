import { EmbedBuilder } from "discord.js";

export const colors = {
  brand: 0xd9_77_06,
  success: 0x22_c5_5e,
  error: 0xef_44_44,
  warning: 0xf5_9e_0b,
} as const;

/** The base for every embed the bot sends. Chain EmbedBuilder methods on the result. */
export const embed = (description?: string): EmbedBuilder => {
  const built = new EmbedBuilder().setColor(colors.brand);
  return description === undefined ? built : built.setDescription(description);
};

export const successEmbed = (description: string): EmbedBuilder =>
  embed(description).setColor(colors.success);

export const errorEmbed = (description: string): EmbedBuilder =>
  embed(description).setColor(colors.error);

export const warningEmbed = (description: string): EmbedBuilder =>
  embed(description).setColor(colors.warning);
