import { PermissionFlagsBits, type GuildTextBasedChannel } from "discord.js";

import { defineCommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";

import { imagePageArgs, imagePages } from "../components/image-pages.ts";
import { requireImageSearch } from "../google.ts";
import { findImages } from "../image-results.ts";
import { clearImageCooldown, takeImageCooldown } from "../images.service.ts";

// The query is stored in the page buttons' custom IDs, which are capped at 100 characters.
const MAX_QUERY_LENGTH = 60;

const isNsfw = (channel: GuildTextBasedChannel): boolean =>
  channel.isThread() ? (channel.parent?.nsfw ?? false) : channel.nsfw;

export const imageCommand = defineCommand({
  name: "image",
  description: "Search Google for images",
  aliases: ["img", "search"],
  options: { query: opt.string("What to search for").max(MAX_QUERY_LENGTH).rest() },
  run: async (ctx, { query }) => {
    requireImageSearch();
    const safe = !isNsfw(ctx.channel);
    takeImageCooldown(ctx.user.id, ctx.member.permissions.has(PermissionFlagsBits.Administrator));
    try {
      await ctx.defer();
      const images = await findImages(query, safe);
      if (images.length === 0) throw new UserError(`No images found for "${query}".`);
    } catch (error) {
      clearImageCooldown(ctx.user.id);
      throw error;
    }
    await imagePages.reply(ctx, { args: imagePageArgs(query, safe) });
  },
});
