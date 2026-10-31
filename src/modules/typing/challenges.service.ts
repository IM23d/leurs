import { UserError } from "#core/errors.ts";

import { pickWords, scoreAttempt, type TypingResult } from "./typing.service.ts";

/** How long a challenge waits for an answer, and how long the race runs once accepted. */
export const CHALLENGE_LIFETIME_MS = 10 * 60 * 1000;
/** A test nobody answered in this time is dropped, so a message days later is not scored. */
export const TEST_LIFETIME_MS = 10 * 60 * 1000;

export interface Challenge {
  readonly id: string;
  readonly challengerId: string;
  readonly challengedId: string;
  readonly words: readonly string[];
  readonly guildId: string;
  readonly channelId: string;
  readonly createdAt: number;
  acceptedAt?: number;
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
  readonly guildId: string;
  readonly channelId: string;
  readonly now: number;
}

/** When the challenge ends: ten minutes after it was sent, or after it was accepted. */
export const challengeDeadline = (challenge: Challenge): number =>
  (challenge.acceptedAt ?? challenge.createdAt) + CHALLENGE_LIFETIME_MS;

function newChallenge(
  { challengerId, challengedId, wordCount, guildId, channelId, now }: NewChallenge,
  random: () => number,
): Challenge {
  if (challengerId === challengedId) throw new UserError("You can't challenge yourself.");
  return {
    id: `${challengerId}-${challengedId}-${Math.floor(now / 1000)}`,
    challengerId,
    challengedId,
    words: pickWords(wordCount, random),
    guildId,
    channelId,
    createdAt: now,
    results: new Map(),
  };
}

/**
 * Running tests and open challenges. Kept in memory like the old bot: a restart drops them,
 * which is fine for something that lasts ten minutes at most.
 */
export function createTypingStore(random: () => number = Math.random) {
  const challenges = new Map<string, Challenge>();
  const tests = new Map<string, ActiveTest>();

  /** Challenges sent to the user in this server that they can still accept. */
  const pendingFor = (userId: string, guildId: string, now: number): Challenge[] =>
    [...challenges.values()].filter(
      (challenge) =>
        challenge.challengedId === userId &&
        challenge.guildId === guildId &&
        challenge.acceptedAt === undefined &&
        now < challengeDeadline(challenge),
    );

  const dropTests = (challengeId: string): void => {
    [...tests]
      .filter(([, test]) => test.challengeId === challengeId)
      .forEach(([userId]) => tests.delete(userId));
  };

  return {
    pendingFor,

    startTest(userId: string, test: ActiveTest): void {
      tests.set(userId, test);
    },

    challenge(input: NewChallenge): Challenge {
      const challenge = newChallenge(input, random);
      challenges.set(challenge.id, challenge);
      return challenge;
    },

    /** Accepts a challenge from this server. Without an ID, accepts the newest pending one. */
    accept(userId: string, id: string | undefined, guildId: string, now: number): Challenge {
      const challengeId = id ?? pendingFor(userId, guildId, now).at(-1)?.id;
      if (challengeId === undefined) {
        throw new UserError("You don't have any pending typing challenges.");
      }
      const challenge = challenges.get(challengeId);
      if (challenge?.guildId !== guildId || now >= challengeDeadline(challenge)) {
        throw new UserError("This challenge doesn't exist or has expired.");
      }
      if (challenge.challengedId !== userId) throw new UserError("This challenge is not for you.");
      if (challenge.acceptedAt !== undefined) {
        throw new UserError("You've already accepted this challenge.");
      }
      challenge.acceptedAt = now;
      return challenge;
    },

    /**
     * Removes a challenge and both players' tests once its deadline has passed. Returns the
     * challenge if it was still open, and nothing if it finished or is not due yet.
     */
    expire(id: string, now: number): Challenge | undefined {
      const challenge = challenges.get(id);
      if (!challenge || now < challengeDeadline(challenge)) return undefined;
      challenges.delete(id);
      dropTests(id);
      return challenge;
    },

    /** Scores a message if the author has a test running in that channel. */
    finish(userId: string, channelId: string, typed: string, now: number): Finished | undefined {
      const test = tests.get(userId);
      if (test === undefined) return undefined;
      if (now - test.startedAt > TEST_LIFETIME_MS) {
        tests.delete(userId);
        return undefined;
      }
      if (test.channelId !== channelId) return undefined;
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
