import { and, eq } from "drizzle-orm";

import { db } from "#db/client.ts";

import { cooldowns } from "./cooldowns.schema.ts";

const PERSIST_FROM_SECONDS = 3600;
const memory = new Map<string, number>();

/**
 * Starts a cooldown unless one is running. Returns the milliseconds left on a running cooldown,
 * or 0 when the cooldown was started.
 */
export function takeCooldown(
  key: string,
  userId: string,
  seconds: number,
  now = Date.now(),
): number {
  const expiresAt = now + seconds * 1000;
  if (seconds < PERSIST_FROM_SECONDS) {
    const memoryKey = `${key}:${userId}`;
    const current = memory.get(memoryKey) ?? 0;
    if (current > now) return current - now;
    memory.set(memoryKey, expiresAt);
    return 0;
  }
  const where = and(eq(cooldowns.key, key), eq(cooldowns.userId, userId));
  const current = db().select().from(cooldowns).where(where).get();
  if (current && current.expiresAt.getTime() > now) return current.expiresAt.getTime() - now;
  db()
    .insert(cooldowns)
    .values({ key, userId, expiresAt: new Date(expiresAt) })
    .onConflictDoUpdate({
      target: [cooldowns.key, cooldowns.userId],
      set: { expiresAt: new Date(expiresAt) },
    })
    .run();
  return 0;
}

/** Ends a cooldown early, for example when the command failed and should not count. */
export function clearCooldown(key: string, userId: string): void {
  memory.delete(`${key}:${userId}`);
  db()
    .delete(cooldowns)
    .where(and(eq(cooldowns.key, key), eq(cooldowns.userId, userId)))
    .run();
}
