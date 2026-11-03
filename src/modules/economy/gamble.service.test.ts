import { describe, expect, it } from "vitest";

import { UserError } from "#core/errors.ts";
import { useTestDb } from "#test/helpers/db.ts";

import { gamble } from "./gamble.service.ts";
import { addBalance, getBalance } from "./wallet.service.ts";

useTestDb();

const heads = () => 0.1;
const tails = () => 0.9;

describe("gamble", () => {
  it("doubles the stake on heads", () => {
    expect(gamble("u1", { kind: "coins", coins: 20 }, heads)).toEqual({
      won: true,
      stake: 20,
      balance: 70,
    });
  });

  it("loses the stake on tails", () => {
    expect(gamble("u1", { kind: "all" }, tails)).toEqual({ won: false, stake: 50, balance: 0 });
  });

  it("bets a share of the balance", () => {
    addBalance("u1", 50);
    expect(gamble("u1", { kind: "percent", percent: 25 }, tails).stake).toBe(25);
  });

  it("refuses more than the balance and an empty stake", () => {
    expect(() => gamble("u1", { kind: "coins", coins: 51 }, heads)).toThrow(UserError);
    expect(getBalance("u1")).toBe(50);
    gamble("u1", { kind: "all" }, tails);
    expect(() => gamble("u1", { kind: "all" }, heads)).toThrow(UserError);
    expect(getBalance("u1")).toBe(0);
  });
});
