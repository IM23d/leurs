import { describe, expect, it } from "vitest";

import { BULK_DELETE_MAX_AGE_MS, parsePurgeTarget, planPurge } from "./purge.service.ts";

const now = 100 * 86_400_000;
const message = (id: string, authorId: string, content: string, ageMs = 0) => ({
  id,
  authorId,
  content,
  createdAt: new Date(now - ageMs),
});

const messages = [
  message("5", "a", "Hello there"),
  message("4", "b", "buy cheap stuff"),
  message("3", "a", "more SPAM"),
  message("2", "b", "spam again"),
  message("1", "a", "old spam", BULK_DELETE_MAX_AGE_MS + 1),
];

describe("planPurge", () => {
  it("takes the newest messages up to the amount", () => {
    expect(planPurge(messages, { amount: 2 }, now)).toEqual({ deletable: ["5", "4"], tooOld: 0 });
  });

  it("filters by author and by text, ignoring case", () => {
    expect(planPurge(messages, { amount: 10, authorId: "b" }, now).deletable).toEqual(["4", "2"]);
    expect(planPurge(messages, { amount: 2, contains: "spam" }, now).deletable).toEqual(["3", "2"]);
    expect(
      planPurge(messages, { amount: 10, authorId: "a", contains: "spam" }, now).deletable,
    ).toEqual(["3"]);
  });

  it("counts matching messages too old to bulk-delete", () => {
    expect(planPurge(messages, { amount: 10, contains: "spam" }, now)).toEqual({
      deletable: ["3", "2"],
      tooOld: 1,
    });
  });
});

describe("parsePurgeTarget", () => {
  it("reads counts and time spans", () => {
    expect(parsePurgeTarget("50")).toEqual({ kind: "count", count: 50 });
    expect(parsePurgeTarget("30m")).toEqual({ kind: "since", ms: 1_800_000 });
    expect(parsePurgeTarget("1mon")).toEqual({ kind: "since", ms: 2_592_000_000 });
  });

  it.each(["0", "101", "soon", ""])("rejects %j", (text) => {
    expect(parsePurgeTarget(text)).toBeUndefined();
  });
});

it("keeps only messages from the time span", () => {
  expect(planPurge(messages, { since: now - 1000 }, now)).toEqual({
    deletable: ["5", "4", "3", "2"],
    tooOld: 0,
  });
});
