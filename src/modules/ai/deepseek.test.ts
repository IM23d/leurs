import { describe, expect, it } from "vitest";

import { assistantRequest } from "./assistant.ts";
import { buildChatRequest, readAnswer } from "./deepseek.ts";

describe("buildChatRequest", () => {
  it("builds a chat request with a system and a user message", () => {
    expect(buildChatRequest("Be brief.", "Hi", { maxTokens: 100, temperature: 0.5 })).toEqual({
      model: "deepseek-chat",
      messages: [
        { role: "system", content: "Be brief." },
        { role: "user", content: "Hi" },
      ],
      temperature: 0.5,
      max_tokens: 100,
    });
  });

  it("asks for JSON when told to", () => {
    const request = buildChatRequest("Answer in JSON.", "Hi", {
      maxTokens: 10,
      temperature: 0,
      json: true,
    });
    expect(request.response_format).toEqual({ type: "json_object" });
  });

  it("keeps the old assistant limits", () => {
    const request = assistantRequest("What is 2 + 2?");
    expect(request).toMatchObject({ max_tokens: 750, temperature: 0.7 });
    expect(request.messages.at(-1)).toEqual({ role: "user", content: "What is 2 + 2?" });
  });
});

describe("readAnswer", () => {
  it("reads the first choice", () => {
    expect(readAnswer({ choices: [{ message: { role: "assistant", content: " 4 \n" } }] })).toBe(
      "4",
    );
  });

  it("reads a missing answer as empty", () => {
    expect(readAnswer({ choices: [] })).toBe("");
    expect(readAnswer({ choices: [{ message: { content: null } }] })).toBe("");
  });
});
