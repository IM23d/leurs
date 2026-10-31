import type { Client } from "discord.js";
import { and, eq } from "drizzle-orm";
import type { z } from "zod";

import { db } from "#db/client.ts";

import { scheduledTasks } from "./tasks.schema.ts";

interface PendingTask<TPayload> {
  readonly id: number;
  readonly runAt: Date;
  readonly payload: TPayload;
}

/** The part of a task the scheduler needs, with the payload type erased. */
export interface RunnableTask {
  readonly kind: string;
  /** Validates the stored payload, then runs the task. */
  execute(payload: unknown, client: Client<true>): Promise<void>;
}

/** Work that runs at a later time and survives restarts, such as a reminder or an unmute. */
export interface Task<TPayload> extends RunnableTask {
  schedule(runAt: Date, payload: TPayload): number;
  cancel(id: number): boolean;
  pending(): PendingTask<TPayload>[];
}

interface TaskDefinition<TPayload> {
  kind: string;
  payload: z.ZodType<TPayload>;
  run: (payload: TPayload, client: Client<true>) => Promise<void>;
}

export function defineTask<TPayload>(definition: TaskDefinition<TPayload>): Task<TPayload> {
  const ofKind = eq(scheduledTasks.kind, definition.kind);
  return {
    kind: definition.kind,
    execute: (payload, client) => definition.run(definition.payload.parse(payload), client),
    schedule: (runAt, payload) =>
      db()
        .insert(scheduledTasks)
        .values({ kind: definition.kind, runAt, payload: definition.payload.parse(payload) })
        .returning({ id: scheduledTasks.id })
        .get().id,
    cancel: (id) =>
      db()
        .delete(scheduledTasks)
        .where(and(ofKind, eq(scheduledTasks.id, id)))
        .run().changes > 0,
    pending: () =>
      db()
        .select()
        .from(scheduledTasks)
        .where(ofKind)
        .orderBy(scheduledTasks.runAt)
        .all()
        .map((row) => ({ ...row, payload: definition.payload.parse(row.payload) })),
  };
}
