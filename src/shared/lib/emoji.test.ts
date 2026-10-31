import { describe, expect, it } from "vitest";

import { parseEmoji, reactionEmojiKey } from "./emoji.ts";

describe("parseEmoji", () => {
  it("reads custom emojis by ID", () => {
    expect(parseEmoji("<:pog:123456789012345678>")).toEqual({
      key: "123456789012345678",
      text: "<:pog:123456789012345678>",
      customId: "123456789012345678",
    });
    expect(parseEmoji("<a:dance:123456789012345678>")?.key).toBe("123456789012345678");
  });

  it("reads Unicode emojis and drops the variation selector from the key", () => {
    expect(parseEmoji("👍")?.key).toBe("👍");
    expect(parseEmoji("❤️")).toEqual({ key: "❤", text: "❤️", customId: undefined });
  });

  it("rejects text and several emojis", () => {
    expect(parseEmoji("hello")).toBeUndefined();
    expect(parseEmoji("👍👍")).toBeUndefined();
    expect(parseEmoji(":pog:")).toBeUndefined();
  });
});

describe("reactionEmojiKey", () => {
  it("matches the keys parseEmoji gives", () => {
    expect(reactionEmojiKey({ id: "123456789012345678", name: "pog" })).toBe("123456789012345678");
    expect(reactionEmojiKey({ id: null, name: "❤️" })).toBe(parseEmoji("❤")?.key);
    expect(reactionEmojiKey({ id: null, name: null })).toBeUndefined();
  });
});
