export interface Token {
  readonly value: string;
  /** Index in the source text where the token starts, quotes included. */
  readonly start: number;
}

const TOKEN = /"([^"]*)"|(\S+)/g;

/** Splits on whitespace. Double quotes group words: `"New York" 3d` gives two tokens. */
export function tokenize(text: string): Token[] {
  return [...text.matchAll(TOKEN)].map((match) => ({
    value: match[1] ?? match[2] ?? "",
    start: match.index,
  }));
}
