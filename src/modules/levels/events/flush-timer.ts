import type { Client } from "discord.js";

import { defineEvent } from "#core/events.ts";
import { logger } from "#shared/lib/logger.ts";

import { flushActivity, syncVoiceSessions } from "../activity.service.ts";

import { voiceUserIds } from "./voice-time.ts";

const FLUSH_INTERVAL_MS = 30_000;

export function flush(): void {
  try {
    flushActivity();
  } catch (error) {
    logger.error({ err: error }, "Writing levels failed");
  }
}

const syncVoice = (client: Client): void => {
  syncVoiceSessions(voiceUserIds(client));
};

/** Starts sessions for members already in voice, then re-syncs and writes gains every 30 seconds. */
export const flushTimerEvent = defineEvent({
  name: "clientReady",
  once: true,
  run: (client) => {
    syncVoice(client);
    setInterval(() => {
      syncVoice(client);
      flush();
    }, FLUSH_INTERVAL_MS).unref();
    return Promise.resolve();
  },
});

/** Ends the sessions of members of a server the bot just left, unless they are in voice elsewhere. */
export const guildLeaveEvent = defineEvent({
  name: "guildDelete",
  run: (guild) => {
    syncVoice(guild.client);
    return Promise.resolve();
  },
});
