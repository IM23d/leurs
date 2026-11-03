import { time, TimestampStyles, type EmbedBuilder, type User } from "discord.js";

import type { ImageUsage } from "#modules/images/api.ts";
import { truncate } from "#shared/lib/text.ts";
import { embed } from "#shared/ui/embeds.ts";

import type { AiUsage } from "./ai.service.ts";
import type { Language } from "./languages.ts";
import { splitText } from "./split-text.ts";
import type { Translation } from "./translation.ts";

// Discord's limits for an embed description and a field value.
const DESCRIPTION_LIMIT = 4096;
const FIELD_LIMIT = 1024;
const PROMPT_PREVIEW = 100;
// The model names the source language, so cap it to keep the title under 256 characters.
const LANGUAGE_NAME_LIMIT = 100;

/** One embed per chunk, so long answers arrive as several messages. */
export function answerEmbeds(answer: string, prompt: string): EmbedBuilder[] {
  const chunks = splitText(answer, DESCRIPTION_LIMIT);
  const parts = chunks.length > 0 ? chunks : ["The AI did not answer. Try asking differently."];
  return parts.map((part, index) => {
    const built = index === 0 ? embed(part).setTitle("AI answer") : embed(part);
    return index === parts.length - 1
      ? built.setFooter({ text: `Prompt: ${truncate(prompt, PROMPT_PREVIEW)}` })
      : built;
  });
}

export function translationEmbed(
  translation: Translation,
  original: string,
  target: Language,
  author?: User,
): EmbedBuilder {
  const built = embed(truncate(translation.text || "(empty)", DESCRIPTION_LIMIT))
    .setTitle(`${truncate(translation.source, LANGUAGE_NAME_LIMIT)} → ${target.name}`)
    .addFields({ name: "Original", value: truncate(original, FIELD_LIMIT) });
  return author
    ? built.setAuthor({ name: author.displayName, iconURL: author.displayAvatarURL() })
    : built;
}

const nextUtcMidnight = (now: number) => {
  const date = new Date(now);
  return new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate() + 1));
};

const configured = (yes: boolean) => (yes ? "Configured" : "Not configured");

export interface UsageView {
  readonly ai: AiUsage;
  readonly images: ImageUsage;
  readonly aiConfigured: boolean;
  readonly imagesConfigured: boolean;
  readonly now: number;
}

export function usageEmbed({ ai, images, aiConfigured, imagesConfigured, now }: UsageView) {
  const top =
    ai.top.map(({ userId, requests }) => `<@${userId}>: ${requests}/${ai.limit}`).join("\n") ||
    "No requests today";
  const aiLines = [
    `**Requests today:** ${ai.requests} by ${ai.users} users`,
    `**On cooldown:** ${ai.usersOnCooldown} users`,
    `**DeepSeek:** ${configured(aiConfigured)}`,
  ];
  const imageLines = [
    `**Searches today:** ${images.searches}/${images.limit}`,
    `**On cooldown:** ${images.usersOnCooldown} users`,
    `**Google:** ${configured(imagesConfigured)}`,
  ];
  return embed(`Limits reset ${time(nextUtcMidnight(now), TimestampStyles.RelativeTime)}.`)
    .setTitle("AI and image usage")
    .addFields(
      { name: "AI", value: aiLines.join("\n"), inline: true },
      { name: "Images", value: imageLines.join("\n"), inline: true },
      { name: "Top AI users today", value: top },
    );
}
