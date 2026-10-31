import { describe, expect, it } from "vitest";

import {
  BULK_DELETE_MAX_AGE_MS,
  parsePurgeTarget,
  planPurge,
  purgeScope,
  readLeadingWords,
} from "./purge.service.ts";

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

describe("purgeScope", () => {
  it("reads the latest 100 for a plain count, further back with a filter", () => {
    expect(purgeScope({ kind: "count", count: 5 }, false, now)).toEqual({
      scanLimit: 100,
      since: undefined,
      count: 5,
    });
    expect(purgeScope({ kind: "count", count: 5 }, true, now).scanLimit).toBe(1000);
  });

  it("uses the time span, or the last 14 days without an amount", () => {
    expect(purgeScope({ kind: "since", ms: 60_000 }, true, now).since).toBe(now - 60_000);
    expect(purgeScope(undefined, true, now).since).toBe(now - BULK_DELETE_MAX_AGE_MS);
  });
});

describe("readLeadingWords", () => {
  const none = { amount: undefined, duplicates: undefined };

  it("moves a leading amount and the duplicates word out of the text filter", () => {
    expect(readLeadingWords({ ...none, contains: "30m dupes spam" })).toEqual({
      amount: { kind: "since", ms: 1_800_000 },
      duplicates: true,
      contains: "spam",
    });
    expect(readLeadingWords({ ...none, contains: "duplicates 20" })).toEqual({
      amount: { kind: "count", count: 20 },
      duplicates: true,
      contains: undefined,
    });
  });

  it("leaves plain text alone", () => {
    const values = { ...none, contains: "buy now" };
    expect(readLeadingWords(values)).toBe(values);
  });
});

describe("duplicates", () => {
  const chat = [
    message("6", "b", "hi"),
    message("5", "a", "  HELLO   there "),
    message("4", "b", "spam"),
    message("3", "a", ""),
    message("2", "b", "spam"),
    message("1", "a", "hello there"),
  ];

  it("deletes repeats and keeps the first copy", () => {
    expect(planPurge(chat, { duplicates: true }, now).deletable).toEqual(["5", "4"]);
  });

  it("only checks the given number of latest messages", () => {
    expect(planPurge(chat, { duplicates: true, amount: 4 }, now).deletable).toEqual([]);
  });

  it("combines with a user filter", () => {
    expect(planPurge(chat, { duplicates: true, authorId: "b" }, now).deletable).toEqual(["4"]);
  });
});
