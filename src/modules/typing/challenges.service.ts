import { UserError } from "#core/errors.ts";

import { pickWords, scoreAttempt, type TypingResult } from "./typing.service.ts";

export const CHALLENGE_LIFETIME_MS = 10 * 60 * 1000;

export interface Challenge {
  readonly id: string;
  readonly challengerId: string;
  readonly challengedId: string;
  readonly words: readonly string[];
  readonly channelId: string;
  readonly createdAt: number;
  accepted: boolean;
  readonly results: Map<string, TypingResult>;
}

export interface ActiveTest {
  readonly words: readonly string[];
  readonly startedAt: number;
  readonly channelId: string;
  readonly challengeId?: string;
}

export type Finished =
  | { readonly kind: "solo"; readonly result: TypingResult }
  | { readonly kind: "waiting"; readonly result: TypingResult }
  | { readonly kind: "complete"; readonly result: TypingResult; readonly challenge: Challenge };

interface NewChallenge {
  readonly challengerId: string;
  readonly challengedId: string;
  readonly wordCount: number;
  readonly channelId: string;
  readonly now: number;
}

/**
 * Running tests and open challenges. Kept in memory like the old bot: a restart drops them,
 * which is fine for something that lasts ten minutes at most.
 */
export function createTypingStore(random: () => number = Math.random) {
  const challenges = new Map<string, Challenge>();
  const tests = new Map<string, ActiveTest>();

  const pendingFor = (userId: string, now: number): Challenge[] =>
    [...challenges.values()].filter(
      (challenge) =>
        challenge.challengedId === userId &&
        !challenge.accepted &&
        now - challenge.createdAt < CHALLENGE_LIFETIME_MS,
    );

  return {
    pendingFor,

    startTest(userId: string, test: ActiveTest): void {
      tests.set(userId, test);
    },

    challenge({ challengerId, challengedId, wordCount, channelId, now }: NewChallenge): Challenge {
      if (challengerId === challengedId) throw new UserError("You can't challenge yourself.");
      const challenge: Challenge = {
        id: `${challengerId}-${challengedId}-${Math.floor(now / 1000)}`,
        challengerId,
        challengedId,
        words: pickWords(wordCount, random),
        channelId,
        createdAt: now,
        accepted: false,
        results: new Map(),
      };
      challenges.set(challenge.id, challenge);
      return challenge;
    },

    /** Without an ID, accepts the newest pending challenge. */
    accept(userId: string, id: string | undefined, now: number): Challenge {
      const challengeId = id ?? pendingFor(userId, now).at(-1)?.id;
      if (challengeId === undefined) {
        throw new UserError("You don't have any pending typing challenges.");
      }
      const challenge = challenges.get(challengeId);
      if (!challenge) throw new UserError("This challenge doesn't exist or has expired.");
      if (challenge.challengedId !== userId) throw new UserError("This challenge is not for you.");
      if (challenge.accepted) throw new UserError("You've already accepted this challenge.");
      challenge.accepted = true;
      return challenge;
    },

    /** Removes a challenge that was not finished in time. Returns it if it was still open. */
    expire(id: string): Challenge | undefined {
      const challenge = challenges.get(id);
      challenges.delete(id);
      return challenge;
    },

    /** Scores a message if the author has a test running in that channel. */
    finish(userId: string, channelId: string, typed: string, now: number): Finished | undefined {
      const test = tests.get(userId);
      if (test?.channelId !== channelId) return undefined;
      tests.delete(userId);
      const result = scoreAttempt(test.words, typed, now - test.startedAt);
      const challenge =
        test.challengeId === undefined ? undefined : challenges.get(test.challengeId);
      if (!challenge) return { kind: "solo", result };
      challenge.results.set(userId, result);
      if (challenge.results.size < 2) return { kind: "waiting", result };
      challenges.delete(challenge.id);
      return { kind: "complete", result, challenge };
    },
  };
}

export type TypingStore = ReturnType<typeof createTypingStore>;

export const typingStore: TypingStore = createTypingStore();
