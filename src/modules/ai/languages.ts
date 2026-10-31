import type { AutocompleteChoice } from "#core/commands/options.ts";

export interface Language {
  readonly code: string;
  readonly name: string;
}

const language = (code: string, name: string): Language => ({ code, name });

export const ENGLISH = language("en", "English");

/** The languages translation accepts and autocomplete offers. */
const LANGUAGES: readonly Language[] = [
  language("ar", "Arabic"),
  language("bg", "Bulgarian"),
  language("zh", "Chinese"),
  language("hr", "Croatian"),
  language("cs", "Czech"),
  language("da", "Danish"),
  language("nl", "Dutch"),
  ENGLISH,
  language("fi", "Finnish"),
  language("fr", "French"),
  language("de", "German"),
  language("el", "Greek"),
  language("he", "Hebrew"),
  language("hi", "Hindi"),
  language("hu", "Hungarian"),
  language("id", "Indonesian"),
  language("it", "Italian"),
  language("ja", "Japanese"),
  language("ko", "Korean"),
  language("no", "Norwegian"),
  language("fa", "Persian"),
  language("pl", "Polish"),
  language("pt", "Portuguese"),
  language("ro", "Romanian"),
  language("ru", "Russian"),
  language("sr", "Serbian"),
  language("es", "Spanish"),
  language("sv", "Swedish"),
  language("th", "Thai"),
  language("tr", "Turkish"),
  language("uk", "Ukrainian"),
  language("vi", "Vietnamese"),
];

/** Reads a language code or English name, such as "de" or "German". */
export function findLanguage(text: string): Language | undefined {
  const wanted = text.trim().toLowerCase();
  return LANGUAGES.find(({ code, name }) => code === wanted || name.toLowerCase() === wanted);
}

export const languageChoices = (query: string): AutocompleteChoice[] => {
  const wanted = query.trim().toLowerCase();
  return LANGUAGES.filter(
    ({ code, name }) => code.startsWith(wanted) || name.toLowerCase().includes(wanted),
  ).map(({ code, name }) => ({ name, value: code }));
};
