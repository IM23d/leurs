import { z } from "zod";

import { UserError } from "#core/errors.ts";

const FORTUNE_URL = "https://api.viewbits.com/v1/fortunecookie?mode=random";
const TIMEOUT_MS = 10_000;
const UNAVAILABLE = "The fortune cookie jar is empty right now. Try again later.";

// The API sometimes sends quotes as literal "’" text instead of the character.
const ESCAPED_QUOTES: readonly (readonly [string, string])[] = [
  [String.raw`‘`, "'"],
  [String.raw`’`, "'"],
  [String.raw`“`, '"'],
  [String.raw`”`, '"'],
];

const fortuneSchema = z.object({ text: z.string().trim().min(1) });

/** Reads the fortune text from an API response, or undefined when there is none. */
export function parseFortune(json: unknown): string | undefined {
  const parsed = fortuneSchema.safeParse(json);
  return parsed.success
    ? ESCAPED_QUOTES.reduce(
        (text, [escaped, character]) => text.replaceAll(escaped, character),
        parsed.data.text,
      )
    : undefined;
}

export async function getFortune(): Promise<string> {
  const response = await fetch(FORTUNE_URL, { signal: AbortSignal.timeout(TIMEOUT_MS) }).catch(
    () => undefined,
  );
  const json: unknown = response?.ok ? await response.json().catch(() => undefined) : undefined;
  const fortune = parseFortune(json);
  if (fortune === undefined) throw new UserError(UNAVAILABLE);
  return fortune;
}
