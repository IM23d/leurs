import { desc, eq, gt, sql } from "drizzle-orm";

import { UserError } from "#core/errors.ts";
import { db } from "#db/client.ts";
import { utcDay } from "#shared/lib/day.ts";
import { formatDuration } from "#shared/lib/duration.ts";

import { aiUsage } from "./ai.schema.ts";

export const AI_COOLDOWN_MS = 30_000;
export const AI_DAILY_LIMIT = 30;
const TOP_USERS = 5;

interface RequestOptions {
  /** Administrators skip the cooldown and the daily limit. Their requests still count. */
  readonly exempt: boolean;
  /** Prompts have a cooldown, translations only count against the daily limit. */
  readonly cooldown: boolean;
  readonly now?: number;
}

/** Counts one AI request, or throws a UserError when the user is on cooldown or out of requests. */
export function takeAiRequest(
  userId: string,
  { exempt, cooldown, now = Date.now() }: RequestOptions,
): void {
  const day = utcDay(now);
  db().transaction(() => {
    const row = db().select().from(aiUsage).where(eq(aiUsage.userId, userId)).get();
    const requests = row?.day === day ? row.requests : 0;
    const lastPromptAt = row?.lastPromptAt ?? null;
    if (!exempt) {
      const left = cooldown && lastPromptAt ? lastPromptAt.getTime() + AI_COOLDOWN_MS - now : 0;
      if (left > 0) throw new UserError(`You can use AI again in ${formatDuration(left)}.`);
      if (requests >= AI_DAILY_LIMIT) {
        throw new UserError(
          `You've used all ${AI_DAILY_LIMIT} AI requests for today. The limit resets at midnight UTC.`,
        );
      }
    }
    const values = {
      day,
      requests: requests + 1,
      lastPromptAt: cooldown && !exempt ? new Date(now) : lastPromptAt,
    };
    db()
      .insert(aiUsage)
      .values({ userId, ...values })
      .onConflictDoUpdate({ target: aiUsage.userId, set: values })
      .run();
  });
}

export interface AiUsage {
  readonly requests: number;
  readonly users: number;
  readonly usersOnCooldown: number;
  readonly limit: number;
  /** The heaviest users today, most requests first. */
  readonly top: readonly { readonly userId: string; readonly requests: number }[];
}

export function getAiUsage(now = Date.now()): AiUsage {
  const today = eq(aiUsage.day, utcDay(now));
  const totals = db()
    .select({
      requests: sql<number>`coalesce(sum(${aiUsage.requests}), 0)`,
      users: sql<number>`count(*)`,
    })
    .from(aiUsage)
    .where(today)
    .get();
  const onCooldown = db()
    .select({ count: sql<number>`count(*)` })
    .from(aiUsage)
    .where(gt(aiUsage.lastPromptAt, new Date(now - AI_COOLDOWN_MS)))
    .get();
  const top = db()
    .select({ userId: aiUsage.userId, requests: aiUsage.requests })
    .from(aiUsage)
    .where(today)
    .orderBy(desc(aiUsage.requests), aiUsage.userId)
    .limit(TOP_USERS)
    .all();
  return {
    requests: totals?.requests ?? 0,
    users: totals?.users ?? 0,
    usersOnCooldown: onCooldown?.count ?? 0,
    limit: AI_DAILY_LIMIT,
    top,
  };
}

/** Clears every count and cooldown. */
export function resetAiUsage(): void {
  db().delete(aiUsage).run();
}
