import { z } from "zod";

import { config } from "#app/config.ts";
import { UserError } from "#core/errors.ts";

const SEARCH_URL = "https://www.googleapis.com/customsearch/v1";
const RESULTS = 10;
const TIMEOUT_MS = 10_000;

export interface ImageResult {
  readonly title: string;
  readonly url: string;
  /** The site the image is on, e.g. "example.com". */
  readonly source: string;
  /** The page the image is on. */
  readonly pageUrl: string;
}

const searchResponse = z.object({
  items: z
    .array(
      z.object({
        title: z.string().catch("No title"),
        link: z.string(),
        displayLink: z.string().catch(""),
        image: z.object({ contextLink: z.string() }).optional(),
      }),
    )
    .default([]),
});

export const mapGoogleImages = (json: unknown): ImageResult[] =>
  searchResponse.parse(json).items.map((item) => ({
    title: item.title,
    url: item.link,
    source: item.displayLink,
    pageUrl: item.image?.contextLink ?? item.link,
  }));

function keys(): { key: string; cx: string } {
  const { GOOGLE_API_KEY: key, GOOGLE_CSE_ID: cx } = config();
  if (!key || !cx) throw new UserError("Image search is not configured.");
  return { key, cx };
}

export const isImageSearchConfigured = (): boolean => {
  const { GOOGLE_API_KEY, GOOGLE_CSE_ID } = config();
  return Boolean(GOOGLE_API_KEY && GOOGLE_CSE_ID);
};

/** Throws when the Google keys are missing, so commands fail before doing any work. */
export const requireImageSearch = (): void => void keys();

export async function fetchGoogleImages(query: string): Promise<ImageResult[]> {
  const params = new URLSearchParams({
    ...keys(),
    q: query,
    searchType: "image",
    num: String(RESULTS),
  });
  const response = await fetch(`${SEARCH_URL}?${params.toString()}`, {
    signal: AbortSignal.timeout(TIMEOUT_MS),
  });
  if (!response.ok) {
    throw new Error(`Google image search answered with status ${response.status}`);
  }
  return mapGoogleImages(await response.json());
}
