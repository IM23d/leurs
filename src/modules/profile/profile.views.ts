import type { EmbedBuilder } from "discord.js";

import { embed } from "#shared/ui/embeds.ts";

export const IMAGE_SIZE = 4096;

export const imageEmbed = (title: string, url: string): EmbedBuilder =>
  embed().setTitle(title).setImage(url);
