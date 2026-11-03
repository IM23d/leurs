export interface AttachmentInfo {
  readonly url: string;
  readonly name: string;
  readonly contentType: string | undefined;
  readonly size: number;
}

export interface Snipe<T> {
  readonly message: T;
  readonly deletedAt: Date;
}

/**
 * The last deleted message in each channel, for `ttlMs`. Kept in memory, as in the old bot.
 * Generic over the message so this file stays free of discord.js.
 */
export function createSnipeStore<T>(ttlMs: number) {
  const latest = new Map<string, Snipe<T>>();
  const isFresh = (snipe: Snipe<T>, now: number) => now - snipe.deletedAt.getTime() < ttlMs;
  return {
    remember: (channelId: string, message: T, now = Date.now()): void => {
      // Dropping stale channels here keeps the map from growing without a timer.
      for (const [id, snipe] of latest) if (!isFresh(snipe, now)) latest.delete(id);
      latest.set(channelId, { message, deletedAt: new Date(now) });
    },
    latest: (channelId: string, now = Date.now()): Snipe<T> | undefined => {
      const snipe = latest.get(channelId);
      return snipe && isFresh(snipe, now) ? snipe : undefined;
    },
    clear: (channelId: string): void => {
      latest.delete(channelId);
    },
  };
}

const IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".gif", ".webp"];

export const isImage = (attachment: AttachmentInfo): boolean =>
  (attachment.contentType?.startsWith("image/") ?? false) ||
  IMAGE_EXTENSIONS.some((extension) => attachment.name.toLowerCase().endsWith(extension));

export const formatSize = (bytes: number): string => `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
