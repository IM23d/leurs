import { describe, expect, it } from "vitest";

import { useTestDb } from "#test/helpers/db.ts";

import {
  emojisFor,
  listAutoReactions,
  removeAutoReaction,
  setAutoReaction,
} from "./auto-reactions.service.ts";

useTestDb();

describe("auto reactions", () => {
  it("stores terms in lowercase and replaces the emoji of an existing term", () => {
    setAutoReaction("g1", "Hello", "👋");
    setAutoReaction("g1", "hello", "🙂");
    expect(listAutoReactions("g1")).toEqual([{ guildId: "g1", term: "hello", emoji: "🙂" }]);
  });

  it("matches terms anywhere in the message, ignoring case", () => {
    setAutoReaction("g1", "cat", "🐱");
    setAutoReaction("g1", "good morning", "☀️");
    setAutoReaction("g2", "dog", "🐶");
    expect(emojisFor("g1", "GOOD MORNING, concatenate")).toEqual(["🐱", "☀️"]);
    expect(emojisFor("g1", "a dog")).toEqual([]);
  });

  it("removes a term in any case and reports a missing term", () => {
    setAutoReaction("g1", "cat", "🐱");
    expect(removeAutoReaction("g1", "CAT")?.emoji).toBe("🐱");
    expect(removeAutoReaction("g1", "cat")).toBeUndefined();
    expect(listAutoReactions("g1")).toEqual([]);
  });
});
