import { defineCommand, subcommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";

import { acceptHint, runChallenge, scheduleExpiry, testImage } from "../challenge-flow.ts";
import { CHALLENGE_LIFETIME_MS, typingStore } from "../challenges.service.ts";
import { acceptButton } from "../components/accept-challenge.ts";
import { DEFAULT_WORDS, MAX_WORDS, MIN_WORDS, pickWords } from "../typing.service.ts";
import { acceptedEmbed, challengeEmbed, pendingEmbed, soloTestEmbed } from "../typing.views.ts";

const wordsOption = opt
  .integer(`How many words (default ${DEFAULT_WORDS})`)
  .min(MIN_WORDS)
  .max(MAX_WORDS)
  .optional();

export const typingCommand = defineCommand({
  name: "typing",
  description: "Typing speed tests and challenges",
  subcommands: {
    test: subcommand({
      description: "Take a typing test",
      aliases: ["monkeytype", "mt", "type"],
      options: { words: wordsOption },
      run: async (ctx, { words: count = DEFAULT_WORDS }) => {
        const words = pickWords(count);
        await ctx.reply({
          embeds: [soloTestEmbed(ctx.user, words.length)],
          files: [await testImage(words)],
        });
        typingStore.startTest(ctx.user.id, {
          words,
          startedAt: Date.now(),
          channelId: ctx.channel.id,
        });
        await ctx.reply(
          `${ctx.user.toString()} Your typing test has started! Type the words shown in the image.`,
        );
      },
    }),
    challenge: subcommand({
      description: "Challenge someone to a typing race",
      aliases: ["mtchallenge", "mtc", "challenge"],
      options: { user: opt.member("Who to challenge"), words: wordsOption },
      run: async (ctx, { user, words = DEFAULT_WORDS }) => {
        if (user.user.bot) throw new UserError("You can't challenge a bot.");
        const challenge = typingStore.challenge({
          challengerId: ctx.user.id,
          challengedId: user.id,
          wordCount: words,
          channelId: ctx.channel.id,
          now: Date.now(),
        });
        await ctx.reply({
          embeds: [challengeEmbed(challenge, acceptHint(ctx))],
          components: [acceptButton(challenge)],
        });
        scheduleExpiry(ctx.client, challenge);
      },
    }),
    accept: subcommand({
      description: "Accept a typing challenge",
      aliases: ["accept"],
      options: { id: opt.string("Challenge ID. Leave empty for the newest").optional() },
      run: async (ctx, { id }) => {
        const challenge = typingStore.accept(ctx.user.id, id, Date.now());
        await ctx.reply(acceptedEmbed(challenge));
        await runChallenge(ctx.channel, challenge);
      },
    }),
    list: subcommand({
      description: "List the typing challenges waiting for you",
      aliases: ["mtlist", "mtl", "challenges"],
      run: async (ctx) => {
        const now = Date.now();
        const challenges = typingStore.pendingFor(ctx.user.id, now);
        if (challenges.length === 0) {
          throw new UserError("You don't have any pending typing challenges.");
        }
        const pending = await Promise.all(
          challenges.map(async (challenge) => ({
            challenge,
            challengerName: await ctx.client.users.fetch(challenge.challengerId).then(
              (user) => user.displayName,
              () => "Unknown user",
            ),
          })),
        );
        await ctx.reply(
          pendingEmbed(pending, now, (id) => acceptHint(ctx, id), CHALLENGE_LIFETIME_MS),
        );
      },
    }),
  },
});
