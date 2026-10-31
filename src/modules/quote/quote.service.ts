import { UserError } from "#core/errors.ts";

import { renderQuote } from "./quote-image.ts";

const AVATAR_TIMEOUT_MS = 10_000;

export interface QuotedMessage {
  readonly avatarUrl: string;
  readonly text: string;
  readonly username: string;
}

async function download(url: string): Promise<Buffer> {
  const response = await fetch(url, { signal: AbortSignal.timeout(AVATAR_TIMEOUT_MS) }).catch(
    () => undefined,
  );
  if (!response?.ok) throw new UserError("I couldn't download the avatar. Try again later.");
  return Buffer.from(await response.arrayBuffer());
}

/** Renders a quote image as PNG. */
export async function createQuote({ avatarUrl, text, username }: QuotedMessage): Promise<Buffer> {
  if (text.trim() === "") throw new UserError("That message has no text to quote.");
  return renderQuote({ avatar: await download(avatarUrl), text, username });
}
