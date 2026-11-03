import { expect, it } from "vitest";

import { useTestDb } from "#test/helpers/db.ts";

import {
  latestRemoval,
  pruneReactions,
  reactionHistory,
  recordReaction,
} from "./reaction-log.service.ts";

useTestDb();

const at = (minute: number) => new Date(Date.UTC(2026, 10, 1, 12, minute));
const event = (action: "add" | "remove", minute: number, overrides = {}) => ({
  guildId: "g",
  channelId: "c",
  messageId: "m",
  userId: "u",
  emoji: "👍",
  action,
  at: at(minute),
  ...overrides,
});

it("lists a message's reaction changes newest first, paged", () => {
  recordReaction(event("add", 0));
  recordReaction(event("remove", 5));
  recordReaction(event("add", 6, { userId: "v", emoji: "🔥" }));
  recordReaction(event("add", 7, { messageId: "other" }));
  expect(reactionHistory("g", "m", 0, 2)).toMatchObject({
    total: 3,
    events: [{ userId: "v", action: "add" }, { action: "remove" }],
  });
  expect(reactionHistory("g", "m", 2, 2).events).toMatchObject([{ action: "add", userId: "u" }]);
});

it("finds the latest removal in a channel within the time limit", () => {
  recordReaction(event("remove", 1, { emoji: "😂" }));
  recordReaction(event("remove", 3, { emoji: "💀" }));
  recordReaction(event("add", 4));
  recordReaction(event("remove", 9, { channelId: "elsewhere" }));
  expect(latestRemoval("c", at(0))?.emoji).toBe("💀");
  expect(latestRemoval("c", at(5))).toBeUndefined();
});

it("prunes old events", () => {
  recordReaction(event("add", 0));
  recordReaction(event("add", 10));
  expect(pruneReactions(at(5))).toBe(1);
  expect(reactionHistory("g", "m", 0, 10).total).toBe(1);
});
