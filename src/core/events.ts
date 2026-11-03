import type { ClientEvents } from "discord.js";

export interface EventHandler<K extends keyof ClientEvents = keyof ClientEvents> {
  readonly name: K;
  readonly once?: boolean;
  readonly run: (...args: ClientEvents[K]) => Promise<void>;
}

/** Listens to a discord.js client event. Errors are logged by the app, not thrown. */
export const defineEvent = <K extends keyof ClientEvents>(handler: EventHandler<K>): EventHandler =>
  handler as unknown as EventHandler;
