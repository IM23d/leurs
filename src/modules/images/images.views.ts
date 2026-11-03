import type { EmbedBuilder } from "discord.js";

import { embed } from "#shared/ui/embeds.ts";

import type { ImageResult } from "./google.ts";

export const imageEmbed = (
  image: ImageResult,
  query: string,
  page: number,
  pageCount: number,
): EmbedBuilder =>
  embed(image.title || "No title")
    .setTitle(`Image search: ${query}`)
    .setImage(image.url)
    .addFields({ name: "Source", value: `[${image.source || "Link"}](${image.pageUrl})` })
    .setFooter({ text: `Image ${page} of ${pageCount}` });
