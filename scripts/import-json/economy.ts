import { z } from "zod";

import { db } from "#db/client.ts";
import { balances, ownedJobs } from "#modules/economy/economy.schema.ts";
import { findJob, MAX_JOBS } from "#modules/economy/job-table.ts";

import type { Importer } from "./source.ts";

// bank.json: { "<userId>": { "wallet": n, "bank": n, ... } }
const coins = z.number().catch(0);
const bank = z.record(
  z.string(),
  z.looseObject({ wallet: coins.optional(), bank: coins.optional() }),
);

// jobs.json: { "current_jobs": [names], "user_jobs": { "<userId>": [names] } }
const jobs = z.looseObject({ user_jobs: z.record(z.string(), z.array(z.string())).optional() });

function importBalances(data: z.infer<typeof bank>): number {
  const rows = Object.entries(data).map(([userId, account]) => ({
    userId,
    balance: Math.max(0, Math.floor((account.wallet ?? 0) + (account.bank ?? 0))),
  }));
  rows.forEach((row) => db().insert(balances).values(row).run());
  return rows.length;
}

// The market always offered every job, so current_jobs carries nothing worth keeping.
function importJobs(data: z.infer<typeof jobs>): number {
  const importedAt = Date.now();
  const rows = Object.entries(data.user_jobs ?? {}).flatMap(([userId, names]) =>
    [...new Set(names.map((name) => findJob(name)?.name))]
      .filter((name) => name !== undefined)
      .slice(0, MAX_JOBS)
      .map((job, index) => ({ userId, job, boughtAt: new Date(importedAt + index) })),
  );
  rows.forEach((row) => db().insert(ownedJobs).values(row).run());
  return rows.length;
}

export const economyImporter: Importer = {
  name: "economy",
  run: (source) =>
    importBalances(bank.optional().parse(source.read("bank.json")) ?? {}) +
    importJobs(jobs.optional().parse(source.read("jobs.json")) ?? {}),
};
