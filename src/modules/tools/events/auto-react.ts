import { defineEvent } from "#core/events.ts";
import { logger } from "#shared/lib/logger.ts";

import { emojisFor } from "../auto-reactions.service.ts";

/** Reacts to messages that contain an auto reaction term. */
export const autoReactEvent = defineEvent({
  name: "messageCreate",
  run: async (message) => {
    if (message.author.bot || !message.inGuild() || message.content === "") return;
    // One at a time, so the reactions keep their order.
    for (const emoji of emojisFor(message.guildId, message.content)) {
      await message.react(emoji).catch((error: unknown) => {
        logger.warn({ err: error, emoji, guild: message.guildId }, "Auto reaction failed");
      });
    }
  },
});
