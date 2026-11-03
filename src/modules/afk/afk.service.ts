import { formatDuration } from "#shared/lib/duration.ts";

const MINUTE_MS = 60_000;
// Discord's message times and our clock can differ a little, so messages this close to going AFK
// count as the AFK command itself.
const GRACE_MS = 2000;

export interface AfkStatus {
  readonly reason: string;
  /** When the user went AFK, in milliseconds since the epoch. */
  readonly since: number;
}

/** AFK statuses by user ID. Kept in memory, so a restart clears them, as in the old bot. */
export function createAfkStore() {
  const statuses = new Map<string, AfkStatus>();
  return {
    set: (userId: string, reason: string, now = Date.now()): void => {
      statuses.set(userId, { reason, since: now });
    },
    get: (userId: string): AfkStatus | undefined => statuses.get(userId),
    /**
     * Clears the status of a user who sent a message, and returns it. Messages from before the
     * user went AFK or just after, such as the AFK command itself, do not count.
     */
    returnFrom: (userId: string, messageAt: number): AfkStatus | undefined => {
      const status = statuses.get(userId);
      if (!status || messageAt <= status.since + GRACE_MS) return undefined;
      statuses.delete(userId);
      return status;
    },
  };
}

export const afkStore = createAfkStore();

/** "2 hours, 5 minutes", rounded down to whole minutes. */
export function formatAway(ms: number): string {
  const minutes = Math.floor(ms / MINUTE_MS);
  return minutes < 1 ? "less than a minute" : formatDuration(minutes * MINUTE_MS);
}
