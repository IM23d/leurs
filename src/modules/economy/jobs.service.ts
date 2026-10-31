import { and, eq } from "drizzle-orm";

import { UserError } from "#core/errors.ts";
import { db } from "#db/client.ts";

import { ownedJobs } from "./economy.schema.ts";
import { findJob, MAX_JOBS, type Job } from "./job-table.ts";
import { addBalance, getBalance, takeBalance, type Random } from "./wallet.service.ts";

export interface Shift {
  readonly job: Job;
  readonly bonus: number;
}

/** The user's jobs in the order they bought them. */
export const ownedJobsOf = (userId: string): Job[] =>
  db()
    .select({ job: ownedJobs.job })
    .from(ownedJobs)
    .where(eq(ownedJobs.userId, userId))
    .orderBy(ownedJobs.boughtAt)
    .all()
    .map((row) => findJob(row.job))
    .filter((job) => job !== undefined);

function requireJob(name: string): Job {
  const job = findJob(name);
  if (!job) throw new UserError(`\`${name}\` is not a job. See the list with \`jobs\`.`);
  return job;
}

/** Buys a job. Returns the job and the balance after paying. */
export function buyJob(
  userId: string,
  name: string,
  now = new Date(),
): { job: Job; balance: number } {
  const job = requireJob(name);
  return db().transaction(() => {
    const owned = ownedJobsOf(userId);
    if (owned.some((candidate) => candidate.name === job.name)) {
      throw new UserError(`You already have the ${job.name} job.`);
    }
    if (owned.length >= MAX_JOBS) {
      throw new UserError(`You can have at most ${MAX_JOBS} jobs. Remove one first.`);
    }
    const balance = takeBalance(userId, job.cost);
    if (balance === undefined) {
      throw new UserError(
        `You need ${job.cost} coins for this job and have ${getBalance(userId)}.`,
      );
    }
    db().insert(ownedJobs).values({ userId, job: job.name, boughtAt: now }).run();
    return { job, balance };
  });
}

/** Quits a job without a refund, like the old bot. */
export function removeJob(userId: string, name: string): Job {
  const job = requireJob(name);
  const removed = db()
    .delete(ownedJobs)
    .where(and(eq(ownedJobs.userId, userId), eq(ownedJobs.job, job.name)))
    .run();
  if (removed.changes === 0) throw new UserError(`You don't have the ${job.name} job.`);
  return job;
}

/** Works one shift at every owned job: base pay, plus the bonus when the roll hits. */
export function work(
  userId: string,
  random: Random = Math.random,
): { shifts: Shift[]; earned: number; balance: number } {
  const shifts = ownedJobsOf(userId).map((job) => ({
    job,
    bonus: random() < job.bonusChance ? job.bonusAmount : 0,
  }));
  if (shifts.length === 0) {
    throw new UserError("You don't have a job yet. Buy one with `jobs buy`.");
  }
  const earned = shifts.reduce((sum, shift) => sum + shift.job.basePay + shift.bonus, 0);
  return { shifts, earned, balance: addBalance(userId, earned) };
}
