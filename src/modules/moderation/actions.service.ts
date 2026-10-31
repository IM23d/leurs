import { and, desc, eq } from "drizzle-orm";

import { UserError } from "#core/errors.ts";
import { db } from "#db/client.ts";
import { formatDuration } from "#shared/lib/duration.ts";

import { modActions, type ModAction } from "./moderation.schema.ts";

type ActionType = "warn" | "ban" | "kick" | "mute" | "jail";

/** Discord does not allow a timeout longer than 28 days. */
export const MAX_TIMEOUT_MS = 28 * 86_400_000;

export function checkTimeoutDuration(ms: number): void {
  if (ms > MAX_TIMEOUT_MS) {
    throw new UserError(`A mute can last at most ${formatDuration(MAX_TIMEOUT_MS)}.`);
  }
}

interface NewAction {
  guildId: string;
  userId: string;
  /** Null for automod. */
  moderatorId: string | null;
  action: ActionType;
  reason?: string | undefined;
  durationMs?: number | undefined;
}

export function recordAction(input: NewAction, now = new Date()): ModAction {
  return db()
    .insert(modActions)
    .values({
      ...input,
      reason: input.reason ?? null,
      durationMs: input.durationMs ?? null,
      createdAt: now,
    })
    .returning()
    .get();
}

/** Every action against a member in a server, newest first. */
export const listActions = (guildId: string, userId: string): ModAction[] =>
  db()
    .select()
    .from(modActions)
    .where(and(eq(modActions.guildId, guildId), eq(modActions.userId, userId)))
    .orderBy(desc(modActions.createdAt), desc(modActions.id))
    .all();

/** How often each action happened, in order of first appearance in `actions`. */
export const countActions = (actions: readonly ModAction[]): Map<string, number> =>
  actions.reduce(
    (counts, { action }) => counts.set(action, (counts.get(action) ?? 0) + 1),
    new Map<string, number>(),
  );
