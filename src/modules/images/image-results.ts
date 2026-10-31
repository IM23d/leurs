import { fetchGoogleImages, type ImageResult } from "./google.ts";
import { countImageSearch } from "./images.service.ts";

const MAX_CACHED_QUERIES = 50;

// Result pages read from here, so browsing does not cost a Google search per click.
const cache = new Map<string, readonly ImageResult[]>();

// Safe and unfiltered results are cached apart, so NSFW channel results never reach other channels.
const keyOf = (query: string, safe: boolean) =>
  `${safe ? "safe" : "off"}:${query.trim().toLowerCase()}`;

/** Cached results for a query, or a new Google search counted against the daily limit. */
export async function findImages(
  query: string,
  safe: boolean,
  search: (query: string, safe: boolean) => Promise<ImageResult[]> = fetchGoogleImages,
  now = Date.now(),
): Promise<readonly ImageResult[]> {
  const key = keyOf(query, safe);
  const cached = cache.get(key);
  if (cached) return cached;
  countImageSearch(now);
  const results = await search(query, safe);
  cache.set(key, results);
  const oldest = cache.keys().next();
  if (cache.size > MAX_CACHED_QUERIES && !oldest.done) cache.delete(oldest.value);
  return results;
}
