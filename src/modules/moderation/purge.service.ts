import { parseDuration } from "#shared/lib/duration.ts";

/** Discord refuses to bulk-delete messages older than 14 days. */
export const BULK_DELETE_MAX_AGE_MS = 14 * 86_400_000;
export const MAX_PURGE = 100;
/** A time-based purge stops after this many messages, so a typo cannot run for minutes. */
export const MAX_TIME_PURGE = 1000;

/** What to delete: a number of messages, or everything from the last `ms` milliseconds. */
export type PurgeTarget =
  | { readonly kind: "count"; readonly count: number }
  | { readonly kind: "since"; readonly ms: number };

/** Reads "50" as a count and "30m", "1d" or "1mon" as a time span. */
export function parsePurgeTarget(text: string): PurgeTarget | undefined {
  if (/^\d+$/.test(text)) {
    const count = Number(text);
    return count >= 1 && count <= MAX_PURGE ? { kind: "count", count } : undefined;
  }
  const ms = parseDuration(text);
  return ms === undefined ? undefined : { kind: "since", ms };
}

interface PurgeCandidate {
  readonly id: string;
  readonly authorId: string;
  readonly content: string;
  readonly createdAt: Date;
}

interface PurgeFilter {
  /** At most this many matching messages. */
  readonly amount?: number | undefined;
  /** Only messages sent at or after this time, in milliseconds. */
  readonly since?: number | undefined;
  readonly authorId?: string | undefined;
  readonly contains?: string | undefined;
}

interface PurgePlan {
  readonly deletable: string[];
  /** Matching messages too old to bulk-delete. */
  readonly tooOld: number;
}

/** Picks up to `amount` matching messages from `messages`, which run newest first. */
export function planPurge(
  messages: readonly PurgeCandidate[],
  { amount = Number.POSITIVE_INFINITY, since = 0, authorId, contains }: PurgeFilter,
  now = Date.now(),
): PurgePlan {
  const text = contains?.toLowerCase();
  const matching = messages
    .filter((message) => message.createdAt.getTime() >= since)
    .filter((message) => authorId === undefined || message.authorId === authorId)
    .filter((message) => text === undefined || message.content.toLowerCase().includes(text))
    .slice(0, amount);
  const isRecent = (message: PurgeCandidate) =>
    now - message.createdAt.getTime() < BULK_DELETE_MAX_AGE_MS;
  const deletable = matching.filter(isRecent).map((message) => message.id);
  return { deletable, tooOld: matching.length - deletable.length };
}
