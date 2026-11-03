import { defineEvent } from "#core/events.ts";
import { logger } from "#shared/lib/logger.ts";

import { pruneReactions, RETENTION_MS } from "../reaction-log.service.ts";

const PRUNE_MS = 86_400_000;

const prune = () => {
  try {
    pruneReactions(new Date(Date.now() - RETENTION_MS));
  } catch (error) {
    logger.error({ err: error }, "Reaction log cleanup failed");
  }
};

/** Deletes reaction history older than a week, once a day. */
export const pruneReactionsEvent = defineEvent({
  name: "clientReady",
  once: true,
  run: () => {
    prune();
    setInterval(prune, PRUNE_MS).unref();
    return Promise.resolve();
  },
});
