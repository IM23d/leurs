import { describe, expect, it } from "vitest";

import { UserError } from "#core/errors.ts";
import { useTestDb } from "#test/helpers/db.ts";

import {
  clearImageCooldown,
  countImageSearch,
  DAILY_SEARCH_LIMIT,
  IMAGE_COOLDOWN_MS,
  imageUsage,
  resetImageUsage,
  takeImageCooldown,
} from "./images.service.ts";

const NOON = Date.UTC(2026, 0, 10, 12);

describe("image cooldown", () => {
  useTestDb();

  it("blocks a second search until the cooldown ends", () => {
    takeImageCooldown("1", false, NOON);
    expect(() => {
      takeImageCooldown("1", false, NOON + 1000);
    }).toThrow("4 minutes, 59 seconds");
    expect(() => {
      takeImageCooldown("1", false, NOON + IMAGE_COOLDOWN_MS);
    }).not.toThrow();
  });

  it("skips exempt users and can be cleared", () => {
    takeImageCooldown("1", true, NOON);
    takeImageCooldown("1", true, NOON);
    takeImageCooldown("2", false, NOON);
    clearImageCooldown("2");
    expect(() => {
      takeImageCooldown("2", false, NOON);
    }).not.toThrow();
  });
});

describe("daily search limit", () => {
  useTestDb();

  const searchTimes = (count: number, now: number) => {
    Array.from({ length: count }).forEach(() => {
      countImageSearch(now);
    });
  };

  it("stops at the limit and starts again the next UTC day", () => {
    searchTimes(DAILY_SEARCH_LIMIT, NOON);
    expect(() => {
      countImageSearch(NOON);
    }).toThrow(UserError);
    expect(() => {
      countImageSearch(Date.UTC(2026, 0, 11, 0, 0, 1));
    }).not.toThrow();
  });

  it("reports and resets usage", () => {
    searchTimes(3, NOON);
    takeImageCooldown("1", false, NOON);
    takeImageCooldown("2", false, NOON - IMAGE_COOLDOWN_MS);
    expect(imageUsage(NOON)).toEqual({
      searches: 3,
      limit: DAILY_SEARCH_LIMIT,
      usersOnCooldown: 1,
    });
    resetImageUsage();
    expect(imageUsage(NOON)).toEqual({
      searches: 0,
      limit: DAILY_SEARCH_LIMIT,
      usersOnCooldown: 0,
    });
  });
});
