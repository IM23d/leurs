import { setTimeout as sleep } from "node:timers/promises";

import {
  AttachmentBuilder,
  userMention,
  type Client,
  type GuildTextBasedChannel,
} from "discord.js";

import type { CommandContext } from "#core/commands/context.ts";

import { CHALLENGE_LIFETIME_MS, typingStore, type Challenge } from "./challenges.service.ts";
import { renderWords } from "./typing-image.ts";
import { challengeTestEmbed } from "./typing.views.ts";

const COUNTDOWN_SECONDS = 5;

export const testImage = async (words: readonly string[]): Promise<AttachmentBuilder> =>
  new AttachmentBuilder(await renderWords(words), { name: "typing_test.png" });

/** How to accept from where the user is: the slash subcommand or the old prefix alias. */
export const acceptHint = (ctx: CommandContext, id?: string): string =>
  ctx.source === "slash"
    ? `\`/typing accept${id === undefined ? "" : ` id:${id}`}\``
    : `\`${ctx.prefix}accept${id === undefined ? "" : ` ${id}`}\``;

/** Counts down, shows both players the same words, and starts their timers together. */
export async function runChallenge(
  channel: GuildTextBasedChannel,
  challenge: Challenge,
): Promise<void> {
  const countdown = await channel.send(`Starting in ${COUNTDOWN_SECONDS}...`);
  for (let second = COUNTDOWN_SECONDS - 1; second > 0; second -= 1) {
    await sleep(1000);
    await countdown.edit(`Starting in ${second}...`);
  }
  await sleep(1000);
  await countdown.edit("Go!");

  const challenger = userMention(challenge.challengerId);
  const challenged = userMention(challenge.challengedId);
  await channel.send({
    content: `${challenger} ${challenged}`,
    embeds: [challengeTestEmbed(challenge)],
    files: [await testImage(challenge.words)],
  });
  const test = {
    words: challenge.words,
    startedAt: Date.now(),
    channelId: channel.id,
    challengeId: challenge.id,
  };
  typingStore.startTest(challenge.challengerId, test);
  typingStore.startTest(challenge.challengedId, test);
  await channel.send(
    `The typing test has started! ${challenger} and ${challenged}, type the words shown in the image.`,
  );
}

/** Drops the challenge after ten minutes unless both players finished. */
export function scheduleExpiry(client: Client, challenge: Challenge): void {
  setTimeout(() => {
    if (!typingStore.expire(challenge.id)) return;
    const channel = client.channels.cache.get(challenge.channelId);
    if (!channel?.isSendable()) return;
    void channel
      .send(
        `⏰ The typing challenge between ${userMention(challenge.challengerId)} and ${userMention(challenge.challengedId)} has expired.`,
      )
      .catch(() => undefined);
  }, CHALLENGE_LIFETIME_MS).unref();
}
