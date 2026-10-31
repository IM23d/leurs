import { parseDuration } from "#shared/lib/duration.ts";

/** Discord refuses to bulk-delete messages older than 14 days. */
export const BULK_DELETE_MAX_AGE_MS = 14 * 86_400_000;
export const MAX_PURGE = 100;
/** A time-based purge stops after this many messages, so a typo cannot run for minutes. */
const MAX_TIME_PURGE = 1000;

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
  /**
   * Only messages that repeat an earlier one, keeping the first copy. With `amount`, the last
   * `amount` messages are checked instead of `amount` messages being deleted.
   */
  readonly duplicates?: boolean | undefined;
}

interface PurgePlan {
  readonly deletable: string[];
  /** Matching messages too old to bulk-delete. */
  readonly tooOld: number;
}

/** Picks up to `amount` matching messages from `messages`, which run newest first. */
/** Text that counts as the same message: case and extra spaces are ignored. */
const duplicateKey = (content: string) => content.trim().replaceAll(/\s+/g, " ").toLowerCase();

/** Messages that repeat an older one in the list, which runs newest first. */
function repeats(messages: readonly PurgeCandidate[]): PurgeCandidate[] {
  const seen = new Set<string>();
  const repeated = new Set<PurgeCandidate>();
  for (const message of messages.toReversed()) {
    const key = duplicateKey(message.content);
    if (key === "") continue;
    if (seen.has(key)) repeated.add(message);
    seen.add(key);
  }
  return messages.filter((message) => repeated.has(message));
}

/** Picks the matching messages from `messages`, which run newest first. */
export function planPurge(
  messages: readonly PurgeCandidate[],
  { amount = Number.POSITIVE_INFINITY, since = 0, authorId, contains, duplicates }: PurgeFilter,
  now = Date.now(),
): PurgePlan {
  const text = contains?.toLowerCase();
  const inRange = messages.filter((message) => message.createdAt.getTime() >= since);
  const filtered = (duplicates ? inRange.slice(0, amount) : inRange)
    .filter((message) => authorId === undefined || message.authorId === authorId)
    .filter((message) => text === undefined || message.content.toLowerCase().includes(text));
  const matching = duplicates ? repeats(filtered) : filtered.slice(0, amount);
  const isRecent = (message: PurgeCandidate) =>
    now - message.createdAt.getTime() < BULK_DELETE_MAX_AGE_MS;
  const deletable = matching.filter(isRecent).map((message) => message.id);
  return { deletable, tooOld: matching.length - deletable.length };
}

interface PurgeScope {
  /** How many of the latest messages to read. */
  readonly scanLimit: number;
  /** Only messages sent at or after this time. */
  readonly since: number | undefined;
  /** At most this many matching messages. */
  readonly count: number | undefined;
}

/**
 * How far back to look. A plain count reads the latest 100. With a user or text filter the
 * matches can be further back, and without an amount everything from the last 14 days matches.
 */
export function purgeScope(
  target: PurgeTarget | undefined,
  filtered: boolean,
  now: number,
): PurgeScope {
  if (target?.kind === "count") {
    return {
      scanLimit: filtered ? MAX_TIME_PURGE : MAX_PURGE,
      since: undefined,
      count: target.count,
    };
  }
  return {
    scanLimit: MAX_TIME_PURGE,
    since: now - (target?.ms ?? BULK_DELETE_MAX_AGE_MS),
    count: undefined,
  };
}

const DUPLICATE_WORDS = new Set(["duplicates", "duplicate", "dupes", "dupe"]);

interface FreeTextValues {
  amount: PurgeTarget | undefined;
  duplicates: boolean | undefined;
  contains: string | undefined;
}

/**
 * Reads an amount and the word "duplicates" from the start of the text filter, so prefix users
 * can write `-clear @user 30m duplicates` in any order. The parser reads options in order, so
 * anything after the user lands in the text filter.
 */
export function readLeadingWords<T extends FreeTextValues>(values: T): T {
  const words = values.contains?.split(/\s+/) ?? [];
  let { amount, duplicates } = values;
  let used = 0;
  for (const word of words) {
    const target = amount === undefined ? parsePurgeTarget(word) : undefined;
    if (target) amount = target;
    else if (DUPLICATE_WORDS.has(word.toLowerCase())) duplicates = true;
    else break;
    used += 1;
  }
  if (used === 0) return values;
  const rest = words.slice(used).join(" ");
  return { ...values, amount, duplicates, contains: rest === "" ? undefined : rest };
}
