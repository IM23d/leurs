import { describe, expect, it } from "vitest";

import { messageLink, parseMessageRef } from "./message-link.ts";

const g = "111111111111111111";
const c = "222222222222222222";
const m = "333333333333333333";

describe("parseMessageRef", () => {
  it("reads message links, including canary and ptb", () => {
    expect(parseMessageRef(messageLink(g, c, m))).toEqual({
      guildId: g,
      channelId: c,
      messageId: m,
    });
    expect(parseMessageRef(`https://ptb.discord.com/channels/${g}/${c}/${m}`)?.messageId).toBe(m);
  });

  it("reads a bare ID", () => {
    expect(parseMessageRef(m)).toEqual({ guildId: undefined, channelId: undefined, messageId: m });
  });

  it("rejects text", () => {
    expect(parseMessageRef("Pick a role")).toBeUndefined();
    expect(parseMessageRef("123")).toBeUndefined();
  });
});
