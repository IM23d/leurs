import { describe, expect, it } from "vitest";

import { UserError } from "#core/errors.ts";
import { useTestDb } from "#test/helpers/db.ts";

import { buyJob, ownedJobsOf, removeJob, work } from "./jobs.service.ts";
import { addBalance, getBalance } from "./wallet.service.ts";

useTestDb();

const names = (userId: string) => ownedJobsOf(userId).map((job) => job.name);
const at = (ms: number) => new Date(ms);

describe("buyJob", () => {
  it("charges the cost and matches names loosely", () => {
    addBalance("u1", 950);
    expect(buyJob("u1", "artist", at(0)).balance).toBe(0);
    expect(buyJob("u1", "mcdonalds employee", at(1)).job.name).toBe("McDonalds-Employee");
    expect(names("u1")).toEqual(["Artist", "McDonalds-Employee"]);
  });

  it("refuses without enough coins and keeps the balance", () => {
    expect(() => buyJob("u1", "Astronaut")).toThrow(UserError);
    expect(getBalance("u1")).toBe(50);
    expect(names("u1")).toEqual([]);
  });

  it("refuses unknown jobs, duplicates and a fourth job", () => {
    expect(() => buyJob("u1", "Wizard")).toThrow(UserError);
    buyJob("u1", "McDonalds-Employee", at(1));
    expect(() => buyJob("u1", "McDonalds-Employee")).toThrow("already");
    buyJob("u1", "Delivery-Driver", at(2));
    addBalance("u1", 1000);
    buyJob("u1", "Stripper", at(3));
    expect(() => buyJob("u1", "Artist")).toThrow("at most 3");
  });
});

describe("removeJob", () => {
  it("removes an owned job and refuses one the user lacks", () => {
    buyJob("u1", "Delivery-Driver");
    expect(removeJob("u1", "delivery driver").name).toBe("Delivery-Driver");
    expect(names("u1")).toEqual([]);
    expect(() => removeJob("u1", "Delivery-Driver")).toThrow(UserError);
  });
});

describe("work", () => {
  it("pays base pay plus bonuses that hit", () => {
    buyJob("u1", "McDonalds-Employee", at(1));
    buyJob("u1", "Delivery-Driver", at(2));
    const rolls = [0.1, 0.9];
    const result = work("u1", () => rolls.shift() ?? 1);
    expect(result.shifts.map((shift) => shift.bonus)).toEqual([50, 0]);
    expect(result.earned).toBe(75 + 50 + 150);
    expect(result.balance).toBe(50 + 275);
  });

  it("refuses a user without a job", () => {
    expect(() => work("u1")).toThrow(UserError);
    expect(getBalance("u1")).toBe(50);
  });
});
