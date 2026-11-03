import { describe, expect, it } from "vitest";

import { useTestDb } from "#test/helpers/db.ts";

import {
  AI_COOLDOWN_MS,
  AI_DAILY_LIMIT,
  getAiUsage,
  resetAiUsage,
  takeAiRequest,
} from "./ai.service.ts";

const NOON = Date.UTC(2026, 0, 10, 12);
const prompt = { exempt: false, cooldown: true };
const translation = { exempt: false, cooldown: false };

const take =
  (userId: string, options: { exempt: boolean; cooldown: boolean }, now: number) => () => {
    takeAiRequest(userId, { ...options, now });
  };

/** Uses `count` requests without hitting the cooldown. */
const useRequests = (userId: string, count: number, now: number) => {
  Array.from({ length: count }).forEach((_, index) => {
    take(userId, translation, now + index)();
  });
};

describe("AI quota", () => {
  useTestDb();

  it("has a cooldown between prompts", () => {
    take("1", prompt, NOON)();
    expect(take("1", prompt, NOON + 1000)).toThrow("29 seconds");
    expect(take("1", prompt, NOON + AI_COOLDOWN_MS)).not.toThrow();
  });

  it("lets translations skip the cooldown", () => {
    take("1", prompt, NOON)();
    expect(take("1", translation, NOON + 1)).not.toThrow();
  });

  it("stops at the daily limit, shared by prompts and translations", () => {
    useRequests("1", AI_DAILY_LIMIT - 1, NOON);
    take("1", prompt, NOON)();
    expect(take("1", translation, NOON + 1)).toThrow(`all ${AI_DAILY_LIMIT} AI requests`);
    expect(take("1", translation, Date.UTC(2026, 0, 11))).not.toThrow();
  });

  it("does not limit exempt users but still counts them", () => {
    const admin = { exempt: true, cooldown: true };
    useRequests("1", AI_DAILY_LIMIT, NOON);
    expect(take("1", admin, NOON)).not.toThrow();
    expect(take("1", admin, NOON + 1)).not.toThrow();
    expect(getAiUsage(NOON).top).toEqual([{ userId: "1", requests: AI_DAILY_LIMIT + 2 }]);
  });

  it("reports today's usage and resets it", () => {
    useRequests("1", 3, NOON);
    take("2", prompt, NOON)();
    take("3", prompt, Date.UTC(2026, 0, 9))();
    expect(getAiUsage(NOON + 1000)).toEqual({
      requests: 4,
      users: 2,
      usersOnCooldown: 1,
      limit: AI_DAILY_LIMIT,
      top: [
        { userId: "1", requests: 3 },
        { userId: "2", requests: 1 },
      ],
    });
    resetAiUsage();
    expect(take("2", prompt, NOON + 1000)).not.toThrow();
    expect(getAiUsage(NOON + 1000).requests).toBe(1);
  });
});
