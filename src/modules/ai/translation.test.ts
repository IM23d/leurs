import { describe, expect, it } from "vitest";

import { ENGLISH, findLanguage, languageChoices } from "./languages.ts";
import { readTranslation, translationRequest } from "./translation.ts";

describe("translationRequest", () => {
  it("asks for JSON in the target language and sends the text as is", () => {
    const request = translationRequest("Bonjour", ENGLISH);
    expect(request.response_format).toEqual({ type: "json_object" });
    expect(request.messages[0]?.content).toContain("into English");
    expect(request.messages[0]?.content).toContain("JSON");
    expect(request.messages[1]).toEqual({ role: "user", content: "Bonjour" });
  });
});

describe("readTranslation", () => {
  it("reads the model's JSON", () => {
    expect(readTranslation('{"source": "French", "translation": " Hello "}')).toEqual({
      source: "French",
      text: "Hello",
    });
  });

  it("falls back to the raw answer", () => {
    expect(readTranslation("Hello")).toEqual({ source: "Unknown", text: "Hello" });
    expect(readTranslation('{"text": "Hello"}')).toEqual({
      source: "Unknown",
      text: '{"text": "Hello"}',
    });
  });
});

describe("languages", () => {
  it("finds a language by code or name", () => {
    expect(findLanguage("DE")?.name).toBe("German");
    expect(findLanguage("japanese")?.code).toBe("ja");
    expect(findLanguage("hello")).toBeUndefined();
  });

  it("suggests languages for autocomplete", () => {
    expect(languageChoices("fr")).toEqual([{ name: "French", value: "fr" }]);
    expect(languageChoices("").length).toBeGreaterThan(25);
  });
});
