/** Discord refuses to bulk-delete messages older than 14 days. */
export const BULK_DELETE_MAX_AGE_MS = 14 * 86_400_000;
export const MAX_PURGE = 100;

interface PurgeCandidate {
  readonly id: string;
  readonly authorId: string;
  readonly content: string;
  readonly createdAt: Date;
}

interface PurgeFilter {
  readonly amount: number;
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
  { amount, authorId, contains }: PurgeFilter,
  now = Date.now(),
): PurgePlan {
  const text = contains?.toLowerCase();
  const matching = messages
    .filter((message) => authorId === undefined || message.authorId === authorId)
    .filter((message) => text === undefined || message.content.toLowerCase().includes(text))
    .slice(0, amount);
  const isRecent = (message: PurgeCandidate) =>
    now - message.createdAt.getTime() < BULK_DELETE_MAX_AGE_MS;
  const deletable = matching.filter(isRecent).map((message) => message.id);
  return { deletable, tooOld: matching.length - deletable.length };
}
