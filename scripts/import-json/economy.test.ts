import { describe, expect, it } from "vitest";

import { ownedJobsOf } from "#modules/economy/jobs.service.ts";
import { getBalance } from "#modules/economy/wallet.service.ts";
import { useTestDb } from "#test/helpers/db.ts";

import { economyImporter } from "./economy.ts";

useTestDb();

const sourceOf = (files: Record<string, unknown>) => ({ read: (file: string) => files[file] });

describe("economyImporter", () => {
  it("merges wallet and bank and keeps known jobs", () => {
    const rows = economyImporter.run(
      sourceOf({
        "bank.json": { u1: { wallet: 30, bank: 70, last_work: null }, u2: { wallet: -5 } },
        "jobs.json": {
          current_jobs: ["Artist"],
          user_jobs: { u1: ["Artist", "Wizard", "Artist", "Teacher"], u2: [] },
        },
      }),
    );
    expect(rows).toBe(4);
    expect(getBalance("u1")).toBe(100);
    expect(getBalance("u2")).toBe(0);
    expect(ownedJobsOf("u1").map((job) => job.name)).toEqual(["Artist", "Teacher"]);
  });

  it("does nothing without files", () => {
    expect(economyImporter.run(sourceOf({}))).toBe(0);
  });
});
