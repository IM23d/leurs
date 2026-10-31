import { defineEvent } from "#core/events.ts";

import { snapshot, snipes } from "../snipes.ts";

export const rememberDeleted = defineEvent({
  name: "messageDelete",
  run: (message) => {
    // A partial message was not cached, so its content is unknown.
    if (message.partial || message.author.bot || !message.inGuild()) return Promise.resolve();
    snipes.remember(message.channelId, snapshot(message));
    return Promise.resolve();
  },
});
