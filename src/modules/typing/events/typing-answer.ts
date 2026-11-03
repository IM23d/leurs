import type { Message } from "discord.js";

import { defineEvent } from "#core/events.ts";

import { typingStore, type Challenge } from "../challenges.service.ts";
import { compareResults } from "../typing.service.ts";
import { comparisonEmbed, resultEmbed } from "../typing.views.ts";

async function announceWinner(message: Message<true>, challenge: Challenge): Promise<void> {
  const result = (id: string) => {
    const found = challenge.results.get(id);
    if (!found) throw new Error(`Challenge ${challenge.id} has no result for ${id}`);
    return { id, result: found };
  };
  const comparison = compareResults(result(challenge.challengerId), result(challenge.challengedId));
  const [winner, loser] = await Promise.all([
    message.client.users.fetch(comparison.winnerId),
    message.client.users.fetch(comparison.loserId),
  ]);
  await message.channel.send({
    embeds: [comparisonEmbed(comparison, winner, loser, challenge.words.length)],
  });
}

/** Treats the next message from someone with a running test, in that channel, as their answer. */
export const typingAnswerEvent = defineEvent({
  name: "messageCreate",
  run: async (message) => {
    if (message.author.bot || !message.inGuild()) return;
    const finished = typingStore.finish(
      message.author.id,
      message.channelId,
      message.content,
      Date.now(),
    );
    if (!finished) return;
    if (finished.kind === "complete") {
      await announceWinner(message, finished.challenge);
      return;
    }
    await message.channel.send({
      embeds: [resultEmbed(finished.result, message.author, finished.kind === "waiting")],
    });
  },
});
