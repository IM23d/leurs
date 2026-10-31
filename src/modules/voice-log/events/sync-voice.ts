import type { Client } from "discord.js";

import { defineEvent } from "#core/events.ts";
import { logger } from "#shared/lib/logger.ts";

import { heartbeat, prune, reconcile, RETENTION_MS, type Presence } from "../voice-log.service.ts";

const HEARTBEAT_MS = 60_000;
const PRUNE_MS = 86_400_000;

const presences = (client: Client): Presence[] =>
  [...client.guilds.cache.values()].flatMap((guild) =>
    [...guild.voiceStates.cache.values()].flatMap((state) =>
      state.channelId === null || state.member?.user.bot
        ? []
        : [{ guildId: guild.id, channelId: state.channelId, userId: state.id }],
    ),
  );

const safely = (what: string, work: () => void) => () => {
  try {
    work();
  } catch (error) {
    logger.error({ err: error }, what);
  }
};

export const markSeen = safely("Voice log heartbeat failed", () => {
  heartbeat(new Date());
});

/** Matches stored stays to the current voice channels, then keeps them up to date. */
export const syncVoiceEvent = defineEvent({
  name: "clientReady",
  once: true,
  run: (client) => {
    safely("Voice log sync failed", () => {
      reconcile(presences(client), new Date());
    })();
    const pruneOld = safely("Voice log cleanup failed", () => {
      prune(new Date(Date.now() - RETENTION_MS));
    });
    pruneOld();
    setInterval(markSeen, HEARTBEAT_MS).unref();
    setInterval(pruneOld, PRUNE_MS).unref();
    return Promise.resolve();
  },
});
