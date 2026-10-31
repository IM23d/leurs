import { PermissionsBitField, type EmbedBuilder } from "discord.js";

import { formatDuration } from "#shared/lib/duration.ts";
import { joinWithin } from "#shared/lib/text.ts";
import { embed } from "#shared/ui/embeds.ts";

import type { Command, Leaf } from "./define.ts";
import type { AnyOption } from "./options.ts";
import { usage } from "./values.ts";

/** Flags that turn any prefix command into a help request, e.g. `-bday set --help`. */
const HELP_FLAGS = new Set(["--help", "-help"]);

export type HelpTarget =
  | { readonly kind: "command"; readonly command: Command }
  | {
      readonly kind: "leaf";
      readonly command: Command;
      readonly name: string;
      readonly leaf: Leaf;
    };

/** How names are shown: `prefix` for usage lines, `textPrefix` for prefix-only aliases. */
export interface HelpPrefixes {
  readonly prefix: string;
  readonly textPrefix: string;
}

/** Returns the text without a trailing help flag, or undefined when there is no flag. */
export function stripHelpFlag(text: string): string | undefined {
  const words = text.trim().split(/\s+/);
  const last = words.at(-1)?.toLowerCase();
  return last !== undefined && HELP_FLAGS.has(last) ? words.slice(0, -1).join(" ") : undefined;
}

const leafTarget = (command: Command, name: string): HelpTarget | undefined => {
  const leaf = command.leaves.get(name);
  return leaf ? { kind: "leaf", command, name, leaf } : undefined;
};

/** Finds what "bday", "bday set", "buyjob" or "tz set" refers to. Two-word names win. */
export function findHelpTarget(commands: readonly Command[], text: string): HelpTarget | undefined {
  const words = text.trim().toLowerCase().split(/\s+/);
  const [first = "", second] = words;
  const pair = second === undefined ? undefined : `${first} ${second}`;
  const leaves = commands.flatMap((command) =>
    [...command.leaves].map(([name, leaf]) => ({ command, name, leaf })),
  );
  const byPath = (key: string) =>
    leaves.find(
      ({ command, name, leaf }) =>
        (name !== "" && `${command.name} ${name}` === key) || leaf.aliases.includes(key),
    );
  const pairMatch = pair === undefined ? undefined : byPath(pair);
  if (pairMatch) return leafTarget(pairMatch.command, pairMatch.name);
  const command = commands.find((c) => c.name === first || c.aliases.includes(first));
  if (command) {
    return command.leaves.has("") ? leafTarget(command, "") : { kind: "command", command };
  }
  const aliasMatch = byPath(first);
  return aliasMatch ? leafTarget(aliasMatch.command, aliasMatch.name) : undefined;
}

const code = (text: string) => `\`${text}\``;

const permissionNames = (bits: bigint) =>
  new PermissionsBitField(bits)
    .toArray()
    .map((name) => name.replaceAll(/([a-z])([A-Z])/g, "$1 $2"))
    .join(", ");

function accessLines(command: Command, leaf?: Leaf): string[] {
  const permissions = [command.permissions, leaf?.permissions]
    .filter((bits) => bits !== undefined)
    .reduce((all, bits) => all | bits, 0n);
  return [
    ...(command.ownerOnly || leaf?.ownerOnly ? ["**Needs:** bot owner"] : []),
    ...(permissions > 0n ? [`**Needs:** ${permissionNames(permissions)}`] : []),
    ...(leaf?.cooldown === undefined
      ? []
      : [`**Cooldown:** ${formatDuration(leaf.cooldown * 1000)}`]),
  ];
}

/** The aliases of a help page, listed once at the bottom. */
const aliasSection = (
  pairs: readonly (readonly [alias: string, path: string])[],
  textPrefix: string,
) =>
  pairs.length > 0
    ? [
        "",
        "**Aliases**",
        ...pairs.map(
          ([alias, path]) => `${code(`${textPrefix}${alias}`)} for ${code(`${textPrefix}${path}`)}`,
        ),
      ]
    : [];

/** "bday set" is just the command alias plus the subcommand, so it needs no line of its own. */
const isDerived = (command: Command, name: string, alias: string) =>
  command.aliases.some((commandAlias) => alias === `${commandAlias} ${name}`);

const sentence = (text: string) => (/[.!?]$/.test(text) ? text : `${text}.`);

function optionLine(name: string, option: AnyOption): string {
  const { description, placeholder, rest, choices } = option.spec;
  const kind = rest ? `${placeholder}, rest of the message` : placeholder;
  const allowed = choices
    ? ` One of: ${choices.map((c) => code(String(c.value))).join(", ")}.`
    : "";
  return `${code(name)} ${kind}, ${option.required ? "required" : "optional"}. ${sentence(description)}${allowed}`;
}

const pathOf = (command: Command, name: string) =>
  name === "" ? command.name : `${command.name} ${name}`;

/** Help for one runnable command or subcommand: usage, every option, aliases and access. */
export function leafHelp(
  target: HelpTarget & { kind: "leaf" },
  { prefix, textPrefix }: HelpPrefixes,
): EmbedBuilder {
  const { command, name, leaf } = target;
  const path = pathOf(command, name);
  const options = Object.entries(leaf.options);
  const aliases = [...leaf.aliases, ...(name === "" ? command.aliases : [])];
  const lines = [
    leaf.description,
    "",
    `**Usage:** ${code(usage(prefix, path, leaf.options))}`,
    ...accessLines(command, leaf),
    ...(options.length > 0
      ? ["", "**Options**", ...options.map(([key, option]) => optionLine(key, option))]
      : []),
    ...aliasSection(
      aliases.map((alias) => [alias, path] as const),
      textPrefix,
    ),
  ];
  return embed(lines.join("\n"))
    .setTitle(`${prefix}${path}`)
    .setFooter({ text: 'Give options in this order. Put text with spaces in "double quotes".' });
}

/** Help for a command with subcommands: the command first, then a short entry per subcommand. */
export function commandHelp(command: Command, { prefix, textPrefix }: HelpPrefixes): EmbedBuilder {
  const intro = [
    command.description,
    "",
    ...(command.defaultSubcommand === undefined
      ? []
      : [
          `**Default:** ${code(`${textPrefix}${command.name}`)} runs ${code(command.defaultSubcommand)}`,
        ]),
    ...accessLines(command),
    "",
    "**Subcommands**",
  ].join("\n");
  const entries = [...command.leaves].map(
    ([name, leaf]) =>
      `${code(usage(prefix, pathOf(command, name), leaf.options))} ${leaf.description}`,
  );
  const aliases = aliasSection(
    [
      ...command.aliases.map((alias) => [alias, command.name] as const),
      ...[...command.leaves].flatMap(([name, leaf]) =>
        leaf.aliases
          .filter((alias) => !isDerived(command, name, alias))
          .map((alias) => [alias, pathOf(command, name)] as const),
      ),
    ],
    textPrefix,
  ).join("\n");
  const subcommands = joinWithin(entries, {
    reserve: intro.length + aliases.length + 1,
    more: (hidden) => `And ${hidden} more.`,
  });
  return embed(`${intro}\n${subcommands}\n${aliases}`)
    .setTitle(`${prefix}${command.name}`)
    .setFooter({
      text: `Add --help after a subcommand to see its options, e.g. ${textPrefix}${pathOf(command, [...command.leaves.keys()][0] ?? "")} --help`,
    });
}

export const helpFor = (target: HelpTarget, prefixes: HelpPrefixes): EmbedBuilder =>
  target.kind === "command" ? commandHelp(target.command, prefixes) : leafHelp(target, prefixes);
