import { userMention, type EmbedBuilder, type User } from "discord.js";

import { colors, embed } from "#shared/ui/embeds.ts";

import type { Challenge } from "./challenges.service.ts";
import { analysis, rating, type Comparison, type TypingResult } from "./typing.service.ts";

const challengeColor = colors.warning;

const instructions = (timer: string, last: string) =>
  [
    "• Type all words in a single message",
    "• Be careful with capitalization and punctuation",
    `• ${timer}`,
    `• ${last}`,
  ].join("\n");

const typeThese = (count: number) =>
  `Type the following ${count} words as fast and accurately as possible.`;

export const soloTestEmbed = (user: User, count: number): EmbedBuilder =>
  embed(typeThese(count))
    .setTitle("🖮 Monkeytype typing test")
    .addFields({
      name: "Instructions",
      value: instructions(
        "The timer starts when you see the image",
        "Your typing speed and accuracy will be calculated",
      ),
    })
    .setImage("attachment://typing_test.png")
    .setFooter({ text: `Typing test for ${user.displayName} | ${count} words` });

export const challengeTestEmbed = (challenge: Challenge): EmbedBuilder =>
  embed(typeThese(challenge.words.length))
    .setColor(challengeColor)
    .setTitle("⚔️ Challenge typing test")
    .addFields(
      {
        name: "Instructions",
        value: instructions(
          "The timer starts now",
          "Your results will be compared with your opponent",
        ),
      },
      {
        name: "Challenge",
        value: `${userMention(challenge.challengerId)} vs ${userMention(challenge.challengedId)}`,
      },
    )
    .setImage("attachment://typing_test.png")
    .setFooter({ text: `Challenge ID: ${challenge.id}` });

export const challengeEmbed = (challenge: Challenge, acceptHint: string): EmbedBuilder =>
  embed(
    `${userMention(challenge.challengerId)} has challenged ${userMention(challenge.challengedId)} to a typing test!`,
  )
    .setColor(challengeColor)
    .setTitle("⚔️ Typing challenge!")
    .addFields(
      {
        name: "Details",
        value: `• ${challenge.words.length} words\n• Both users will type the same text\n• Speed and accuracy will be compared`,
      },
      {
        name: "How to accept",
        value: `${userMention(challenge.challengedId)}, press **Accept** or use ${acceptHint}.`,
      },
    )
    .setFooter({ text: `Challenge ID: ${challenge.id} | Expires in 10 minutes` });

export const acceptedEmbed = (challenge: Challenge): EmbedBuilder =>
  embed(
    `${userMention(challenge.challengedId)} has accepted ${userMention(challenge.challengerId)}'s typing challenge!`,
  )
    .setColor(challengeColor)
    .setTitle("⚔️ Challenge accepted!")
    .addFields({
      name: "Get ready!",
      value: "The typing test will begin shortly. Both users will see the same text.",
    });

const accuracyColor = (accuracy: number) =>
  accuracy > 90 ? colors.success : accuracy > 75 ? colors.warning : colors.error;

export function resultEmbed(result: TypingResult, user: User, waiting = false): EmbedBuilder {
  const built = embed()
    .setColor(accuracyColor(result.accuracy))
    .setTitle("⌨️ Typing test results")
    .addFields(
      { name: "Speed", value: `**${result.wpm.toFixed(1)}** WPM`, inline: true },
      { name: "Accuracy", value: `**${result.accuracy.toFixed(1)}%**`, inline: true },
      { name: "Time", value: `**${result.seconds.toFixed(1)}** seconds`, inline: true },
      {
        name: "Characters",
        value: `Correct: **${result.correctChars}** / Total: **${result.totalChars}**`,
      },
      { name: "Rating", value: rating(result.wpm) },
    )
    .setFooter({ text: `Typing test completed by ${user.displayName}` });
  return waiting
    ? built.addFields({
        name: "Challenge status",
        value: "Waiting for opponent to complete the test...",
      })
    : built;
}

const summary = (result: TypingResult) =>
  [
    `• Speed: **${result.wpm.toFixed(1)}** WPM`,
    `• Accuracy: **${result.accuracy.toFixed(1)}%**`,
    `• Time: **${result.seconds.toFixed(1)}s**`,
  ].join("\n");

export function comparisonEmbed(
  comparison: Comparison,
  winner: User,
  loser: User,
  wordCount: number,
): EmbedBuilder {
  return embed(`**${winner.displayName}** wins the typing challenge!`)
    .setColor(0xff_d7_00)
    .setTitle("⚔️ Typing challenge results")
    .addFields(
      { name: `${winner.displayName}'s results`, value: summary(comparison.winner), inline: true },
      { name: `${loser.displayName}'s results`, value: summary(comparison.loser), inline: true },
      {
        name: "Difference",
        value: `• Speed: **${comparison.wpmDiff.toFixed(1)}** WPM\n• Accuracy: **${comparison.accuracyDiff.toFixed(1)}%**`,
      },
      {
        name: "Analysis",
        value: analysis(comparison.wpmDiff, winner.displayName, loser.displayName),
      },
    )
    .setFooter({ text: `Challenge completed | ${wordCount} words` });
}

export interface PendingChallenge {
  readonly challenge: Challenge;
  readonly challengerName: string;
}

export function pendingEmbed(
  pending: readonly PendingChallenge[],
  now: number,
  acceptHint: (id: string) => string,
  lifetimeMs: number,
): EmbedBuilder {
  const fields = pending.slice(0, 25).map(({ challenge, challengerName }) => {
    const left = Math.max(0, lifetimeMs - (now - challenge.createdAt)) / 1000;
    return {
      name: `Challenge from ${challengerName}`,
      value: [
        `• ${challenge.words.length} words`,
        `• Expires in ${Math.floor(left / 60)}m ${Math.floor(left % 60)}s`,
        `• To accept: ${acceptHint(challenge.id)}`,
      ].join("\n"),
    };
  });
  return embed()
    .setColor(challengeColor)
    .setTitle("📝 Your pending typing challenges")
    .addFields(fields);
}
