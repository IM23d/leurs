/**
 * Splits text into chunks of at most `limit` characters. Prefers to cut at a paragraph, then a
 * line, then a space, so words stay whole when possible.
 */
export function splitText(text: string, limit: number): string[] {
  const chunks: string[] = [];
  let rest = text.trim();
  while (rest.length > limit) {
    const window = rest.slice(0, limit + 1);
    const cut =
      ["\n\n", "\n", " "]
        .map((separator) => window.lastIndexOf(separator))
        .find((index) => index > limit / 2) ?? limit;
    chunks.push(rest.slice(0, cut).trimEnd());
    rest = rest.slice(cut).trimStart();
  }
  return rest === "" ? chunks : [...chunks, rest];
}
