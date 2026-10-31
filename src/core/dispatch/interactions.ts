import {
  MessageFlags,
  type AutocompleteInteraction,
  type ChatInputCommandInteraction,
  type Interaction,
  type RepliableInteraction,
} from "discord.js";

import { slashContext } from "../commands/slash-context.ts";
import { slashValues, usage, ArgumentError } from "../commands/values.ts";
import { parseCustomId } from "../components.ts";
import type { Registry, Route } from "../registry.ts";

import { failureEmbed } from "./failures.ts";
import { runCommand, type RunOptions } from "./run-command.ts";

function routeFor(
  registry: Registry,
  commandName: string,
  subcommand: string | null,
): Route | undefined {
  const command = registry.commands.find((candidate) => candidate.name === commandName);
  const leaf = command?.leaves.get(subcommand ?? "");
  if (!command || !leaf) return undefined;
  return { command, leaf, path: subcommand ? `${command.name} ${subcommand}` : command.name };
}

async function replyWithFailure(
  interaction: RepliableInteraction,
  error: unknown,
  context: Record<string, unknown>,
): Promise<void> {
  const payload = {
    embeds: [failureEmbed(error, context)],
    flags: MessageFlags.Ephemeral,
  } as const;
  await (interaction.deferred || interaction.replied
    ? interaction.followUp(payload)
    : interaction.reply(payload));
}

async function chatInput(
  interaction: ChatInputCommandInteraction<"cached">,
  registry: Registry,
  options: RunOptions,
): Promise<void> {
  const route = routeFor(
    registry,
    interaction.commandName,
    interaction.options.getSubcommand(false),
  );
  if (!route) return;
  try {
    const ctx = slashContext(interaction, registry.commands);
    await runCommand(ctx, route, () => slashValues(interaction, route.leaf.options), options);
  } catch (error) {
    const shown =
      error instanceof ArgumentError
        ? new ArgumentError(
            `${error.message}\nUsage: \`${usage("/", route.path, route.leaf.options)}\``,
          )
        : error;
    await replyWithFailure(interaction, shown, { command: route.path, user: interaction.user.id });
  }
}

async function autocomplete(interaction: AutocompleteInteraction<"cached">, registry: Registry) {
  const route = routeFor(
    registry,
    interaction.commandName,
    interaction.options.getSubcommand(false),
  );
  const focused = interaction.options.getFocused(true);
  const handler = route?.leaf.options[focused.name]?.spec.autocomplete;
  if (!handler) return;
  const choices = await handler(focused.value, {
    guildId: interaction.guildId,
    userId: interaction.user.id,
  });
  await interaction.respond(choices.slice(0, 25));
}

/** Routes slash commands, autocomplete, context menus, buttons, selects and modals. */
export async function handleInteraction(
  interaction: Interaction,
  registry: Registry,
  options: RunOptions,
): Promise<void> {
  if (!interaction.inCachedGuild()) return;
  if (interaction.isChatInputCommand()) {
    await chatInput(interaction, registry, options);
    return;
  }
  if (interaction.isAutocomplete()) {
    await autocomplete(interaction, registry).catch(() => interaction.respond([]));
    return;
  }
  const context = { interaction: interaction.id, user: interaction.user.id };
  try {
    if (interaction.isContextMenuCommand()) {
      const menu = registry.contextMenus.get(interaction.commandName);
      if (menu?.type === "message" && interaction.isMessageContextMenuCommand()) {
        await menu.run(interaction);
      }
      if (menu?.type === "user" && interaction.isUserContextMenuCommand()) {
        await menu.run(interaction);
      }
    } else if (interaction.isMessageComponent() || interaction.isModalSubmit()) {
      const { id, args } = parseCustomId(interaction.customId);
      await registry.components.get(id)?.run(interaction, args);
    }
  } catch (error) {
    await replyWithFailure(interaction, error, context);
  }
}
