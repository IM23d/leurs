import { defineEvent } from "#core/events.ts";

import { parseDailySummary } from "../wordle-parse.ts";
import { saveSummary } from "../wordle.service.ts";

/** Stores the Wordle app's daily summary when it is posted. */
export const recordResultsEvent = defineEvent({
  name: "messageCreate",
  run: (message) => {
    if (!message.inGuild() || !message.author.bot) return Promise.resolve();
    const summary = parseDailySummary(message.content, message.createdAt);
    if (summary) saveSummary(message.guildId, summary);
    return Promise.resolve();
  },
});
