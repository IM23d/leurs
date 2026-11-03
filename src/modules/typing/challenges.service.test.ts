import { beforeEach, describe, expect, it } from "vitest";

import { UserError } from "#core/errors.ts";

import {
  CHALLENGE_LIFETIME_MS,
  createTypingStore,
  TEST_LIFETIME_MS,
  type Challenge,
  type TypingStore,
} from "./challenges.service.ts";

let store: TypingStore;
const NOW = 1_700_000_000_000;

const challenge = (challengerId = "a", challengedId = "b", now = NOW, guildId = "g"): Challenge =>
  store.challenge({ challengerId, challengedId, wordCount: 10, guildId, channelId: "c", now });

beforeEach(() => {
  store = createTypingStore(() => 0);
});

describe("challenges", () => {
  it("rejects challenging yourself", () => {
    expect(() => challenge("a", "a")).toThrow(UserError);
  });

  it("builds the ID from both users and the time in seconds", () => {
    expect(challenge().id).toBe("a-b-1700000000");
  });

  it("accepts the newest pending challenge when no ID is given", () => {
    challenge("a", "b", NOW);
    const newest = challenge("x", "b", NOW + 1000);
    expect(store.accept("b", undefined, "g", NOW + 2000).id).toBe(newest.id);
    expect(store.pendingFor("b", "g", NOW + 2000)).toHaveLength(1);
  });

  it("only lets the challenged user accept, once", () => {
    const { id } = challenge();
    expect(() => store.accept("a", id, "g", NOW)).toThrow("This challenge is not for you.");
    store.accept("b", id, "g", NOW);
    expect(() => store.accept("b", id, "g", NOW)).toThrow(
      "You've already accepted this challenge.",
    );
  });

  it("explains when there is nothing to accept", () => {
    expect(() => store.accept("b", undefined, "g", NOW)).toThrow(
      "You don't have any pending typing challenges.",
    );
    expect(() => store.accept("b", "nope", "g", NOW)).toThrow(
      "This challenge doesn't exist or has expired.",
    );
  });

  it("only accepts challenges from the current server", () => {
    const { id } = challenge("a", "b", NOW, "other");
    expect(store.pendingFor("b", "g", NOW)).toEqual([]);
    expect(() => store.accept("b", undefined, "g", NOW)).toThrow(
      "You don't have any pending typing challenges.",
    );
    expect(() => store.accept("b", id, "g", NOW)).toThrow(
      "This challenge doesn't exist or has expired.",
    );
    expect(store.accept("b", undefined, "other", NOW).id).toBe(id);
  });

  it("hides expired challenges and drops them on expiry", () => {
    const { id } = challenge();
    const deadline = NOW + CHALLENGE_LIFETIME_MS;
    expect(store.pendingFor("b", "g", deadline)).toEqual([]);
    expect(() => store.accept("b", id, "g", deadline)).toThrow("has expired");
    expect(store.expire(id, deadline - 1)).toBeUndefined();
    expect(store.expire(id, deadline)?.id).toBe(id);
    expect(store.expire(id, deadline)).toBeUndefined();
  });

  it("times an accepted challenge from when it was accepted", () => {
    const { id } = challenge();
    const acceptedAt = NOW + CHALLENGE_LIFETIME_MS - 1000;
    store.accept("b", id, "g", acceptedAt);
    expect(store.expire(id, NOW + CHALLENGE_LIFETIME_MS)).toBeUndefined();
    expect(store.expire(id, acceptedAt + CHALLENGE_LIFETIME_MS)?.id).toBe(id);
  });
});

describe("finish", () => {
  it("ignores users without a test and other channels", () => {
    store.startTest("a", { words: ["hi"], startedAt: NOW, channelId: "c" });
    expect(store.finish("b", "c", "hi", NOW + 1000)).toBeUndefined();
    expect(store.finish("a", "other", "hi", NOW + 1000)).toBeUndefined();
    expect(store.finish("a", "c", "hi", NOW + 1000)?.kind).toBe("solo");
    expect(store.finish("a", "c", "hi", NOW + 2000)).toBeUndefined();
  });

  it("waits for both players, then completes the challenge", () => {
    const accepted = store.accept("b", challenge().id, "g", NOW);
    const test = {
      words: accepted.words,
      startedAt: NOW,
      channelId: "c",
      challengeId: accepted.id,
    };
    store.startTest("a", test);
    store.startTest("b", test);
    const typed = accepted.words.join(" ");
    expect(store.finish("a", "c", typed, NOW + 5000)?.kind).toBe("waiting");
    const done = store.finish("b", "c", typed, NOW + 6000);
    expect(done?.kind).toBe("complete");
    expect(done?.kind === "complete" && done.challenge.results.size).toBe(2);
    expect(store.expire(accepted.id, NOW + 2 * CHALLENGE_LIFETIME_MS)).toBeUndefined();
  });

  it("drops a test nobody answered in time", () => {
    store.startTest("a", { words: ["hi"], startedAt: NOW, channelId: "c" });
    expect(store.finish("a", "c", "hi", NOW + TEST_LIFETIME_MS + 1)).toBeUndefined();
    expect(store.finish("a", "c", "hi", NOW + 1000)).toBeUndefined();
  });

  it("drops both players' tests when the challenge expires", () => {
    const accepted = store.accept("b", challenge().id, "g", NOW);
    const test = { words: ["hi"], startedAt: NOW, channelId: "c", challengeId: accepted.id };
    store.startTest("a", test);
    store.startTest("b", test);
    store.startTest("x", { words: ["hi"], startedAt: NOW, channelId: "c" });
    store.expire(accepted.id, NOW + CHALLENGE_LIFETIME_MS);
    expect(store.finish("a", "c", "hi", NOW + 1000)).toBeUndefined();
    expect(store.finish("b", "c", "hi", NOW + 1000)).toBeUndefined();
    expect(store.finish("x", "c", "hi", NOW + 1000)?.kind).toBe("solo");
  });
});
