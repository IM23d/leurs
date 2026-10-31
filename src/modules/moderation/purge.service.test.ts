import { describe, expect, it } from "vitest";

import { BULK_DELETE_MAX_AGE_MS, planPurge } from "./purge.service.ts";

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
