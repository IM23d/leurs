import { describe, expect, it } from "vitest";

import { useTestDb } from "#test/helpers/db.ts";

import {
  disableClownboard,
  enableClownboard,
  findPost,
  getClownboard,
  removePost,
  savePost,
  startVote,
  topClowns,
  updateClownboard,
} from "./clownboard.service.ts";

useTestDb();

const vote = (messageId: string, authorId: string) => ({
  messageId,
  guildId: "g",
  channelId: "c",
  authorId,
  startedBy: "starter",
  postedAt: new Date(0),
});

/** Starts a vote and marks it as posted to the clownboard. */
const posted = (messageId: string, authorId: string) => {
  startVote(vote(messageId, authorId));
  savePost({ ...vote(messageId, authorId), boardMessageId: `b${messageId}`, count: 3 });
};

describe("settings", () => {
  it("is off until enabled, and keeps changes when the channel moves", () => {
    expect(getClownboard("g")).toBeUndefined();
    expect(updateClownboard("g", { threshold: 3 })).toBeUndefined();
    expect(enableClownboard("g", "c1")).toMatchObject({
      emoji: "🤡",
      threshold: 3,
      cooldownSeconds: 21_600,
    });
    updateClownboard("g", { threshold: 3 });
    expect(enableClownboard("g", "c2")).toMatchObject({ channelId: "c2", threshold: 3 });
    expect(disableClownboard("g")).toBe(true);
    expect(getClownboard("g")).toBeUndefined();
  });
});

describe("votes and posts", () => {
  it("starts a vote once per message", () => {
    expect(startVote(vote("m1", "alex"))).toBe(true);
    expect(startVote(vote("m1", "alex"))).toBe(false);
    expect(findPost("g", "m1")).toMatchObject({ boardMessageId: null, count: 0 });
  });

  it("finds a post by either message and ranks only posted messages", () => {
    posted("m1", "alex");
    posted("m2", "alex");
    posted("m3", "mika");
    startVote(vote("m4", "robi"));
    expect(findPost("g", "bm2")?.messageId).toBe("m2");
    expect(topClowns("g", 10)).toEqual([
      { authorId: "alex", posts: 2 },
      { authorId: "mika", posts: 1 },
    ]);
    expect(removePost("m1")?.boardMessageId).toBe("bm1");
    expect(topClowns("g", 10)[0]).toEqual({ authorId: "alex", posts: 1 });
  });
});
