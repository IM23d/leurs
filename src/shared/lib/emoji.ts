const CUSTOM_EMOJI = /^<a?:\w{2,32}:(\d{17,20})>$/;
const UNICODE_EMOJI = /^\p{RGI_Emoji}$/v;
const VARIATION_SELECTOR = String.fromCodePoint(0xfe_0f);

export interface ParsedEmoji {
  /** What a reaction is matched on: the ID of a custom emoji, or the Unicode emoji itself. */
  readonly key: string;
  /** What the bot reacts with and shows in lists. */
  readonly text: string;
  /** Set for custom emojis only. */
  readonly customId: string | undefined;
}

// Clients send some emojis with and some without the variation selector, so keys drop it.
const unicodeKey = (text: string): string => text.replaceAll(VARIATION_SELECTOR, "");

/** Reads a custom emoji such as `<:name:123>` or a single Unicode emoji. */
export function parseEmoji(input: string): ParsedEmoji | undefined {
  const text = input.trim();
  const customId = CUSTOM_EMOJI.exec(text)?.[1];
  if (customId) return { key: customId, text, customId };
  const isUnicode = UNICODE_EMOJI.test(text) || UNICODE_EMOJI.test(text + VARIATION_SELECTOR);
  return isUnicode ? { key: unicodeKey(text), text, customId: undefined } : undefined;
}

/** The key of an emoji on a reaction, matching `ParsedEmoji.key`. */
export function reactionEmojiKey(emoji: {
  readonly id: string | null;
  readonly name: string | null;
}): string | undefined {
  return emoji.id ?? (emoji.name === null ? undefined : unicodeKey(emoji.name));
}
