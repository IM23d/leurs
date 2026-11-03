import { PermissionFlagsBits } from "discord.js";

import { defineCommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";

import { takeAiRequest } from "../ai.service.ts";
import { answerEmbeds } from "../ai.views.ts";
import { ask } from "../assistant.ts";
import { requireDeepseek } from "../deepseek.ts";

export const aiCommand = defineCommand({
  name: "ai",
  description: "Ask the AI a question",
  options: { prompt: opt.string("What to ask").rest() },
  run: async (ctx, { prompt }) => {
    requireDeepseek();
    takeAiRequest(ctx.user.id, {
      exempt: ctx.member.permissions.has(PermissionFlagsBits.Administrator),
      cooldown: true,
    });
    await ctx.defer();
    const answer = await ask(prompt);
    for (const part of answerEmbeds(answer, prompt)) await ctx.reply(part);
  },
});
