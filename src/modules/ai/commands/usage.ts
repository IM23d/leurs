import { defineCommand, subcommand } from "#core/commands/define.ts";
import { imageUsage, isImageSearchConfigured, resetImageUsage } from "#modules/images/api.ts";
import { successEmbed } from "#shared/ui/embeds.ts";

import { getAiUsage, resetAiUsage } from "../ai.service.ts";
import { usageEmbed } from "../ai.views.ts";
import { isDeepseekConfigured } from "../deepseek.ts";

export const usageCommand = defineCommand({
  name: "usage",
  description: "Show or reset AI and image search usage",
  ownerOnly: true,
  defaultSubcommand: "view",
  subcommands: {
    view: subcommand({
      description: "Show today's AI and image search usage",
      aliases: ["ai_stats", "imgstats"],
      run: async (ctx) => {
        const now = Date.now();
        await ctx.reply(
          usageEmbed({
            ai: getAiUsage(now),
            images: imageUsage(now),
            aiConfigured: isDeepseekConfigured(),
            imagesConfigured: isImageSearchConfigured(),
            now,
          }),
        );
      },
    }),
    reset: subcommand({
      description: "Reset every AI and image search count and cooldown",
      aliases: ["ai_reset_cooldowns", "ai_reset_count", "img_reset_cooldowns", "img_reset_count"],
      run: async (ctx) => {
        resetAiUsage();
        resetImageUsage();
        await ctx.reply(successEmbed("Reset AI and image search counts and cooldowns."));
      },
    }),
  },
});
