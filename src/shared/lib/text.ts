/** Discord's limit for an embed description. */
const EMBED_DESCRIPTION_LIMIT = 4096;

/** Cuts text to `max` characters, ending with an ellipsis when it was cut. */
export const truncate = (text: string, max: number): string =>
  text.length > max ? `${text.slice(0, max - 1)}…` : text;

/**
 * Joins as many entries as fit in `limit` characters, and at most `max` entries. When some are
 * left out, ends with `more(leftOutCount)`. `reserve` keeps room for text added after the result.
 */
export function joinWithin(
  entries: readonly string[],
  {
    limit = EMBED_DESCRIPTION_LIMIT,
    separator = "\n",
    reserve = 0,
    max = Number.POSITIVE_INFINITY,
    more,
  }: {
    limit?: number;
    separator?: string;
    reserve?: number;
    max?: number;
    more: (hidden: number) => string;
  },
): string {
  const room = limit - reserve - separator.length - more(entries.length).length;
  const shown: string[] = [];
  let used = 0;
  for (const entry of entries) {
    if (shown.length >= max) break;
    used += entry.length + (shown.length > 0 ? separator.length : 0);
    if (used > room) break;
    shown.push(entry);
  }
  const hidden = entries.length - shown.length;
  return [...shown, ...(hidden > 0 ? [more(hidden)] : [])].join(separator);
}
