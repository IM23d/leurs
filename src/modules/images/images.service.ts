import { eq, gt, sql } from "drizzle-orm";

import { UserError } from "#core/errors.ts";
import { db } from "#db/client.ts";
import { utcDay } from "#shared/lib/day.ts";
import { formatDuration } from "#shared/lib/duration.ts";

import { imageCooldowns, imageSearchDays } from "./images.schema.ts";

export const IMAGE_COOLDOWN_MS = 5 * 60_000;
export const DAILY_SEARCH_LIMIT = 100;

/** Starts the user's cooldown, or throws while one is running. Exempt users skip it. */
export function takeImageCooldown(userId: string, exempt: boolean, now = Date.now()): void {
  if (exempt) return;
  db().transaction(() => {
    const last = db().select().from(imageCooldowns).where(eq(imageCooldowns.userId, userId)).get();
    const left = last ? last.searchedAt.getTime() + IMAGE_COOLDOWN_MS - now : 0;
    if (left > 0) throw new UserError(`You can search images again in ${formatDuration(left)}.`);
    const searchedAt = new Date(now);
    db()
      .insert(imageCooldowns)
      .values({ userId, searchedAt })
      .onConflictDoUpdate({ target: imageCooldowns.userId, set: { searchedAt } })
      .run();
  });
}

/** Ends a cooldown early, when the search failed and should not count. */
export function clearImageCooldown(userId: string): void {
  db().delete(imageCooldowns).where(eq(imageCooldowns.userId, userId)).run();
}

const searchesOn = (day: string) =>
  db().select().from(imageSearchDays).where(eq(imageSearchDays.day, day)).get()?.searches ?? 0;

/** Counts one Google search, or throws when today's global limit is used up. */
export function countImageSearch(now = Date.now()): void {
  const day = utcDay(now);
  db().transaction(() => {
    if (searchesOn(day) >= DAILY_SEARCH_LIMIT) {
      throw new UserError("The daily image search limit is used up. It resets at midnight UTC.");
    }
    db()
      .insert(imageSearchDays)
      .values({ day, searches: 1 })
      .onConflictDoUpdate({
        target: imageSearchDays.day,
        set: { searches: sql`${imageSearchDays.searches} + 1` },
      })
      .run();
  });
}

export interface ImageUsage {
  readonly searches: number;
  readonly limit: number;
  readonly usersOnCooldown: number;
}

export function imageUsage(now = Date.now()): ImageUsage {
  const usersOnCooldown = db()
    .select({ count: sql<number>`count(*)` })
    .from(imageCooldowns)
    .where(gt(imageCooldowns.searchedAt, new Date(now - IMAGE_COOLDOWN_MS)))
    .get()?.count;
  return {
    searches: searchesOn(utcDay(now)),
    limit: DAILY_SEARCH_LIMIT,
    usersOnCooldown: usersOnCooldown ?? 0,
  };
}

/** Clears today's count and every cooldown. */
export function resetImageUsage(): void {
  db().transaction(() => {
    db().delete(imageSearchDays).run();
    db().delete(imageCooldowns).run();
  });
}
