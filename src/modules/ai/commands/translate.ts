import { PermissionFlagsBits } from "discord.js";

import { defineCommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";

import { takeAiRequest } from "../ai.service.ts";
import { translationEmbed } from "../ai.views.ts";
import { requireDeepseek } from "../deepseek.ts";
import { ENGLISH, findLanguage, languageChoices } from "../languages.ts";
import { messageText } from "../message-text.ts";
import { translate } from "../translation.ts";

// Long enough for a message, short enough that the translation fits in one embed.
const MAX_TEXT_LENGTH = 2000;

export const translateCommand = defineCommand({
  name: "translate",
  description: "Translate text, or the message you reply to, with AI",
  aliases: ["t", "tr"],
  // `to` comes first so that "-translate de Hallo" reads the language before the text.
  options: {
    to: opt
      .custom("Language to translate to, English if empty", "language", findLanguage)
      .autocomplete(languageChoices)
      .optional(),
    text: opt.string("Text to translate").max(MAX_TEXT_LENGTH).rest().optional(),
  },
  run: async (ctx, { to = ENGLISH, text }) => {
    requireDeepseek();
    const replied = text === undefined ? await ctx.referencedMessage() : undefined;
    const original = text ?? (replied && messageText(replied));
    if (original === undefined) {
      throw new UserError(
        ctx.source === "slash"
          ? "Give me text to translate, or use Apps > Translate on a message."
          : "Give me text to translate, or reply to a message.",
      );
    }
    takeAiRequest(ctx.user.id, {
      exempt: ctx.member.permissions.has(PermissionFlagsBits.Administrator),
      cooldown: false,
    });
    await ctx.defer();
    const translation = await translate(original, to);
    await ctx.reply(translationEmbed(translation, original, to, replied?.author));
  },
});
