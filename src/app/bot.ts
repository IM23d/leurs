import { Client, Events, GatewayIntentBits, Partials } from "discord.js";

import { handleInteraction } from "#core/dispatch/interactions.ts";
import { handleMessage } from "#core/dispatch/messages.ts";
import { buildRegistry } from "#core/registry.ts";
import { startScheduler } from "#core/tasks/scheduler.ts";
import { getPrefix } from "#modules/settings/api.ts";
import { logger } from "#shared/lib/logger.ts";

import type { Config } from "./config.ts";
import { modules } from "./modules.ts";

const logFailure = (what: string) => (error: unknown) => {
  logger.error({ err: error }, what);
};

/** Creates the client, wires every module and logs in. Returns a function that shuts down. */
export async function startBot(config: Config): Promise<() => Promise<void>> {
  const registry = buildRegistry(modules);
  const client = new Client({
    intents: [
      GatewayIntentBits.Guilds,
      GatewayIntentBits.GuildMembers,
      GatewayIntentBits.GuildMessages,
      GatewayIntentBits.MessageContent,
      GatewayIntentBits.GuildVoiceStates,
      GatewayIntentBits.GuildMessageReactions,
    ],
    partials: [Partials.Message, Partials.Reaction, Partials.User, Partials.GuildMember],
    allowedMentions: { parse: ["users"] },
  });
  const options = { ownerIds: config.OWNER_IDS, getPrefix };

  client.on(Events.InteractionCreate, (interaction) => {
    handleInteraction(interaction, registry, options).catch(logFailure("Interaction failed"));
  });
  client.on(Events.MessageCreate, (message) => {
    handleMessage(message, registry, options).catch(logFailure("Message command failed"));
  });
  for (const event of registry.events) {
    const listener = (...args: unknown[]) => {
      (event.run as (...a: unknown[]) => Promise<void>)(...args).catch(
        logFailure(`Event handler for ${event.name} failed`),
      );
    };
    if (event.once) client.once(event.name, listener);
    else client.on(event.name, listener);
  }

  let stopScheduler: () => void = () => {
    // Replaced once the client is ready.
  };
  client.once(Events.ClientReady, (ready) => {
    stopScheduler = startScheduler(ready, registry.tasks);
    logger.info({ user: ready.user.tag, guilds: ready.guilds.cache.size }, "Bot is ready");
  });

  await client.login(config.DISCORD_TOKEN);
  return async () => {
    stopScheduler();
    await client.destroy();
  };
}
