import { EmbedType, type Message } from "discord.js";
import { describe, expect, it } from "vitest";

import { boardContent, boardMessage } from "./clownboard.views.ts";

const GIF = "https://klipy.com/gifs/ishowspeed-talking-tom-1";

/** Just enough of a message for the clownboard views. */
const message = (
  content: string,
  embeds: { type: EmbedType; url?: string; thumbnail?: string }[],
) =>
  ({
    content,
    channelId: "c",
    url: "https://discord.com/channels/g/c/m",
    createdAt: new Date(0),
    member: { displayName: "alex" },
    author: { displayName: "alex", displayAvatarURL: () => "https://cdn/avatar.png" },
    attachments: { find: () => undefined },
    embeds: embeds.map(({ type, url, thumbnail }) => ({
      data: { type },
      url: url ?? null,
      image: null,
      thumbnail: thumbnail ? { url: thumbnail } : null,
    })),
  }) as unknown as Message<true>;

describe("clownboard posts", () => {
  it("adds a GIF link below the counter so Discord plays it, and leaves the card text empty", () => {
    const gif = message(GIF, [
      { type: EmbedType.GIFV, url: GIF, thumbnail: "https://x/still.png" },
    ]);
    expect(boardContent(gif, "🤡", 2)).toBe(`🤡 **2** · <#c>\n${GIF}`);
    const card = boardMessage(gif, "🤡", 2).embeds[0]?.data;
    expect(card?.description).toBeUndefined();
    expect(card?.image).toBeUndefined();
  });

  it("uses a link preview's thumbnail as the picture", () => {
    const link = message("look", [{ type: EmbedType.Link, thumbnail: "https://x/preview.png" }]);
    expect(boardContent(link, "🤡", 1)).toBe("🤡 **1** · <#c>");
    expect(boardMessage(link, "🤡", 1).embeds[0]?.data.image?.url).toBe("https://x/preview.png");
  });
});
