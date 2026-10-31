import { describe, expect, it } from "vitest";

import { useTestDb } from "#test/helpers/db.ts";

import {
  disableClownboard,
  enableClownboard,
  findPost,
  getClownboard,
  removePost,
  savePost,
  topClowns,
  updateClownboard,
} from "./clownboard.service.ts";

useTestDb();

const post = (messageId: string, authorId: string, boardMessageId = `b${messageId}`) => ({
  messageId,
  guildId: "g",
  channelId: "c",
  authorId,
  boardMessageId,
  count: 1,
  postedAt: new Date(0),
});

describe("settings", () => {
  it("is off until enabled, and keeps changes when the channel moves", () => {
    expect(getClownboard("g")).toBeUndefined();
    expect(updateClownboard("g", { threshold: 3 })).toBeUndefined();
    expect(enableClownboard("g", "c1")).toMatchObject({
      emoji: "🤡",
      threshold: 1,
      cooldownSeconds: 21_600,
    });
    updateClownboard("g", { threshold: 3 });
    expect(enableClownboard("g", "c2")).toMatchObject({ channelId: "c2", threshold: 3 });
    expect(disableClownboard("g")).toBe(true);
    expect(getClownboard("g")).toBeUndefined();
  });
});

describe("posts", () => {
  it("finds a post by either message and ranks the most clowned members", () => {
    savePost(post("m1", "alex"));
    savePost(post("m2", "alex"));
    savePost(post("m3", "mika"));
    expect(findPost("g", "bm2")?.messageId).toBe("m2");
    expect(findPost("g", "m3")?.authorId).toBe("mika");
    expect(topClowns("g", 10)).toEqual([
      { authorId: "alex", posts: 2 },
      { authorId: "mika", posts: 1 },
    ]);
    expect(removePost("m1")?.boardMessageId).toBe("bm1");
    expect(topClowns("g", 10)[0]).toEqual({ authorId: "alex", posts: 1 });
  });

  it("updates the count of a post that exists", () => {
    savePost(post("m1", "alex"));
    savePost({ ...post("m1", "alex"), count: 4 });
    expect(findPost("g", "m1")?.count).toBe(4);
  });
});
