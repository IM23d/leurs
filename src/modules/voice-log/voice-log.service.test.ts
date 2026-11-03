import { describe, expect, it } from "vitest";

import { useTestDb } from "#test/helpers/db.ts";

import {
  heartbeat,
  history,
  join,
  leave,
  openStays,
  prune,
  reconcile,
} from "./voice-log.service.ts";

useTestDb();

const at = (minutes: number) => new Date(Date.UTC(2026, 9, 31, 18, minutes));
const alice = { guildId: "g1", channelId: "c1", userId: "alice" };
const bob = { guildId: "g1", channelId: "c2", userId: "bob" };

describe("join and leave", () => {
  it("records a stay with join and leave times", () => {
    join(alice, at(0));
    expect(openStays("g1")).toMatchObject([{ userId: "alice", joinedAt: at(0), leftAt: null }]);
    const stay = leave("g1", "alice", at(43));
    expect(stay).toMatchObject({ channelId: "c1", joinedAt: at(0), leftAt: at(43) });
    expect(openStays("g1")).toEqual([]);
  });

  it("ends the old stay when a member moves to another channel", () => {
    join(alice, at(0));
    join({ ...alice, channelId: "c2" }, at(10));
    expect(openStays("g1")).toMatchObject([{ channelId: "c2", joinedAt: at(10) }]);
    expect(history({ guildId: "g1", channelId: "c1" }, 0, 10).stays).toMatchObject([
      { leftAt: at(10) },
    ]);
  });

  it("returns nothing when leaving without a stay", () => {
    expect(leave("g1", "nobody", at(0))).toBeUndefined();
  });
});

describe("history", () => {
  it("lists stays newest first, filtered and paged", () => {
    join(alice, at(0));
    leave("g1", "alice", at(5));
    join(bob, at(10));
    join(alice, at(20));
    expect(history({ guildId: "g1" }, 0, 2)).toMatchObject({
      total: 3,
      stays: [{ userId: "alice", joinedAt: at(20) }, { userId: "bob" }],
    });
    expect(history({ guildId: "g1", userId: "bob" }, 0, 10).total).toBe(1);
    expect(history({ guildId: "other" }, 0, 10).total).toBe(0);
  });
});

describe("reconcile", () => {
  it("ends stays of people who left while the bot was down, at the last time it saw them", () => {
    join(alice, at(0));
    heartbeat(at(30));
    reconcile([bob], at(90));
    expect(history({ guildId: "g1", userId: "alice" }, 0, 1).stays).toMatchObject([
      { leftAt: at(30) },
    ]);
    expect(openStays("g1")).toMatchObject([{ userId: "bob", joinedAt: at(90) }]);
  });

  it("keeps stays of people who are still there", () => {
    join(alice, at(0));
    reconcile([alice], at(90));
    expect(openStays("g1")).toMatchObject([{ userId: "alice", joinedAt: at(0) }]);
  });
});

it("prunes finished stays older than the cut-off", () => {
  join(alice, at(0));
  leave("g1", "alice", at(5));
  join(bob, at(0));
  expect(prune(at(10))).toBe(1);
  expect(history({ guildId: "g1" }, 0, 10).total).toBe(1);
});
