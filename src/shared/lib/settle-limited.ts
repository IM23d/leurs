/**
 * Like `Promise.allSettled(items.map(run))`, but with at most `limit` calls running at once.
 * Use it for APIs that rate-limit bursts, such as Last.fm (error 29).
 */
export async function settleLimited<T, R>(
  items: readonly T[],
  limit: number,
  run: (item: T) => Promise<R>,
): Promise<PromiseSettledResult<R>[]> {
  const results: PromiseSettledResult<R>[] = [];
  // Every worker pulls from the same iterator, so each item runs once.
  const queue = items.entries();
  const worker = async () => {
    for (const [index, item] of queue) {
      results[index] = await run(item).then(
        (value) => ({ status: "fulfilled", value }),
        (reason: unknown) => ({ status: "rejected", reason }),
      );
    }
  };
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, worker));
  return results;
}
