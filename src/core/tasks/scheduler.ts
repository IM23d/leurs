import type { Client } from "discord.js";
import { eq, lte } from "drizzle-orm";

import { db } from "#db/client.ts";
import { logger } from "#shared/lib/logger.ts";

import type { RunnableTask } from "./define-task.ts";
import { scheduledTasks } from "./tasks.schema.ts";

const POLL_INTERVAL_MS = 10_000;
const BATCH_SIZE = 50;

async function runDue(
  client: Client<true>,
  tasks: ReadonlyMap<string, RunnableTask>,
): Promise<void> {
  const due = db()
    .select()
    .from(scheduledTasks)
    .where(lte(scheduledTasks.runAt, new Date()))
    .orderBy(scheduledTasks.runAt)
    .limit(BATCH_SIZE)
    .all();
  for (const row of due) {
    // Delete first so a task that keeps failing does not run forever.
    db().delete(scheduledTasks).where(eq(scheduledTasks.id, row.id)).run();
    const task = tasks.get(row.kind);
    if (!task) {
      logger.warn({ kind: row.kind, id: row.id }, "Dropped a task with an unknown kind");
      continue;
    }
    try {
      await task.execute(row.payload, client);
    } catch (error) {
      logger.error({ err: error, kind: row.kind, id: row.id }, "Scheduled task failed");
    }
  }
}

/** Runs due tasks every few seconds. Returns a function that stops the scheduler. */
export function startScheduler(client: Client<true>, tasks: readonly RunnableTask[]): () => void {
  const byKind = new Map(tasks.map((task) => [task.kind, task]));
  let running = false;
  const tick = () => {
    if (running) return;
    running = true;
    runDue(client, byKind)
      .catch((error: unknown) => {
        logger.error({ err: error }, "Scheduler tick failed");
      })
      .finally(() => {
        running = false;
      });
  };
  tick();
  const timer = setInterval(tick, POLL_INTERVAL_MS);
  return () => {
    clearInterval(timer);
  };
}
