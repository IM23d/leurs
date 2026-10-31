import { beforeEach, describe, expect, it } from "vitest";

import { UserError } from "#core/errors.ts";

import {
  CHALLENGE_LIFETIME_MS,
  createTypingStore,
  type Challenge,
  type TypingStore,
} from "./challenges.service.ts";

let store: TypingStore;
const NOW = 1_700_000_000_000;

const challenge = (challengerId = "a", challengedId = "b", now = NOW): Challenge =>
  store.challenge({ challengerId, challengedId, wordCount: 10, channelId: "c", now });

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
    expect(store.accept("b", undefined, NOW + 2000).id).toBe(newest.id);
    expect(store.pendingFor("b", NOW + 2000)).toHaveLength(1);
  });

  it("only lets the challenged user accept, once", () => {
    const { id } = challenge();
    expect(() => store.accept("a", id, NOW)).toThrow("This challenge is not for you.");
    store.accept("b", id, NOW);
    expect(() => store.accept("b", id, NOW)).toThrow("You've already accepted this challenge.");
  });

  it("explains when there is nothing to accept", () => {
    expect(() => store.accept("b", undefined, NOW)).toThrow(
      "You don't have any pending typing challenges.",
    );
    expect(() => store.accept("b", "nope", NOW)).toThrow(
      "This challenge doesn't exist or has expired.",
    );
  });

  it("hides expired challenges and drops them on expiry", () => {
    const { id } = challenge();
    expect(store.pendingFor("b", NOW + CHALLENGE_LIFETIME_MS)).toEqual([]);
    expect(store.expire(id)?.id).toBe(id);
    expect(store.expire(id)).toBeUndefined();
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
    const accepted = store.accept("b", challenge().id, NOW);
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
    expect(store.expire(accepted.id)).toBeUndefined();
  });

  it("scores a test whose challenge expired on its own", () => {
    const { id } = challenge();
    store.startTest("a", { words: ["hi"], startedAt: NOW, channelId: "c", challengeId: id });
    store.expire(id);
    expect(store.finish("a", "c", "hi", NOW + 1000)?.kind).toBe("solo");
  });
});
