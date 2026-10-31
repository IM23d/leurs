import { defineEvent } from "#core/events.ts";
import { logger } from "#shared/lib/logger.ts";

import { flushActivity, setVoiceActive } from "../activity.service.ts";

import { countsAsVoiceTime } from "./voice-time.ts";

const FLUSH_INTERVAL_MS = 30_000;

export function flush(): void {
  try {
    flushActivity();
  } catch (error) {
    logger.error({ err: error }, "Writing levels failed");
  }
}

/** Starts voice sessions for members already in voice, then writes gains every 30 seconds. */
export const flushTimerEvent = defineEvent({
  name: "clientReady",
  once: true,
  run: (client) => {
    client.guilds.cache
      .flatMap((guild) => guild.voiceStates.cache)
      .filter((state) => !state.member?.user.bot && countsAsVoiceTime(state))
      .forEach((state) => {
        setVoiceActive(state.id, true);
      });
    setInterval(flush, FLUSH_INTERVAL_MS).unref();
    return Promise.resolve();
  },
});
