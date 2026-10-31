import type { Message } from "discord.js";

import { prefixContext } from "../commands/prefix-context.ts";
import { ArgumentError, prefixValues, usage } from "../commands/values.ts";
import { findPrefixRoute, type Registry } from "../registry.ts";

import { failureEmbed } from "./failures.ts";
import { runCommand, type RunOptions } from "./run-command.ts";

export interface MessageOptions extends RunOptions {
  readonly getPrefix: (guildId: string) => string;
}

/** Returns the text after the prefix or a bot mention, or undefined when neither is used. */
function stripPrefix(content: string, prefix: string, botId: string): string | undefined {
  const mention = new RegExp(String.raw`^<@!?${botId}>\s*`).exec(content);
  if (mention) return content.slice(mention[0].length);
  return content.startsWith(prefix) ? content.slice(prefix.length) : undefined;
}

/** Runs prefix commands. Unknown commands are ignored, so stray prefixes in chat stay quiet. */
export async function handleMessage(
  message: Message,
  registry: Registry,
  options: MessageOptions,
): Promise<void> {
  if (message.author.bot || !message.inGuild()) return;
  const prefix = options.getPrefix(message.guildId);
  const text = stripPrefix(message.content, prefix, message.client.user.id);
  if (text === undefined || /^\s/.test(text)) return;
  const found = findPrefixRoute(registry, text);
  if (!found) return;
  const { route, rest } = found;
  const member = message.member ?? (await message.guild.members.fetch(message.author.id));
  const ctx = prefixContext(message, member, prefix, registry.commands);
  try {
    await runCommand(
      ctx,
      route,
      () => prefixValues(rest, message.guild, route.leaf.options),
      options,
    );
  } catch (error) {
    const shown =
      error instanceof ArgumentError
        ? new ArgumentError(
            `${error.message}\nUsage: \`${usage(prefix, route.path, route.leaf.options)}\``,
          )
        : error;
    await ctx.reply({
      embeds: [failureEmbed(shown, { command: route.path, user: message.author.id })],
    });
  }
}
