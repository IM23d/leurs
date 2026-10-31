import { describe, expect, it } from "vitest";

import { useTestDb } from "#test/helpers/db.ts";

import {
  addBalance,
  balanceRanking,
  beg,
  getBalance,
  STARTING_BALANCE,
  takeBalance,
  takeUpTo,
} from "./wallet.service.ts";

useTestDb();

describe("balances", () => {
  it("starts a new user at the starting balance", () => {
    expect(getBalance("u1")).toBe(STARTING_BALANCE);
    expect(addBalance("u1", 10)).toBe(STARTING_BALANCE + 10);
    expect(addBalance("u1", 5)).toBe(STARTING_BALANCE + 15);
  });

  it("takes coins only when the user has enough", () => {
    expect(takeBalance("u1", 30)).toBe(20);
    expect(takeBalance("u1", 21)).toBeUndefined();
    expect(getBalance("u1")).toBe(20);
    expect(takeBalance("u1", 20)).toBe(0);
  });

  it("stops at zero when an admin removes too much", () => {
    expect(takeUpTo("u1", 80)).toEqual({ taken: 50, balance: 0 });
    expect(takeUpTo("u1", 10)).toEqual({ taken: 0, balance: 0 });
    addBalance("u2", 50);
    expect(takeUpTo("u2", 30)).toEqual({ taken: 30, balance: 70 });
  });
});

describe("beg", () => {
  it("pays 0 to 100 coins", () => {
    expect(beg("u1", () => 0)).toEqual({ earned: 0, balance: 50 });
    expect(beg("u1", () => 0.999)).toEqual({ earned: 100, balance: 150 });
  });
});

describe("balanceRanking", () => {
  it("lists users with an account, richest first", () => {
    addBalance("poor", -40);
    addBalance("rich", 100);
    addBalance("other", 0);
    expect(balanceRanking(["poor", "rich", "nobody"])).toEqual([
      { userId: "rich", balance: 150 },
      { userId: "poor", balance: 10 },
    ]);
    expect(balanceRanking([])).toEqual([]);
  });
});
