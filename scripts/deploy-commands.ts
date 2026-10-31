// Registers slash commands and context menus with Discord.
// With DEV_GUILD_ID set, registers them in that server only, where changes show up at once.
import { REST, Routes } from "discord.js";

import { loadConfig } from "#app/config.ts";
import { modules } from "#app/modules.ts";
import { commandJson, contextMenuJson } from "#core/commands/slash.ts";
import { buildRegistry } from "#core/registry.ts";

const config = loadConfig();
const registry = buildRegistry(modules);
const body = [
  ...registry.commands.map(commandJson),
  ...[...registry.contextMenus.values()].map(contextMenuJson),
];

const rest = new REST().setToken(config.DISCORD_TOKEN);
const route = config.DEV_GUILD_ID
  ? Routes.applicationGuildCommands(config.DISCORD_CLIENT_ID, config.DEV_GUILD_ID)
  : Routes.applicationCommands(config.DISCORD_CLIENT_ID);

await rest.put(route, { body });
console.log(
  `Registered ${body.length} commands ${config.DEV_GUILD_ID ? `in server ${config.DEV_GUILD_ID}` : "globally"}.`,
);
