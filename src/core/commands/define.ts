import type { CommandContext } from "./context.ts";
import type { OptionsShape, OptionValues } from "./options.ts";

interface Access {
  /** Discord permissions the member needs, e.g. PermissionFlagsBits.BanMembers. */
  permissions?: bigint;
  /** Only users listed in OWNER_IDS may run it. */
  ownerOnly?: boolean;
}

interface LeafDefinition<TOptions extends OptionsShape> extends Access {
  description: string;
  options?: TOptions;
  /** Extra prefix names. A name may contain a space, e.g. "tz set". */
  aliases?: readonly string[];
  /** Per-user cooldown in seconds. Cooldowns of an hour or more survive restarts. */
  cooldown?: number;
  run: (ctx: CommandContext, values: OptionValues<TOptions>) => Promise<void>;
}

/** A runnable command or subcommand with its option types erased. */
export interface Leaf extends Access {
  readonly description: string;
  readonly options: OptionsShape;
  readonly aliases: readonly string[];
  readonly cooldown: number | undefined;
  readonly run: (ctx: CommandContext, values: Record<string, unknown>) => Promise<void>;
}

export interface Command extends Access {
  readonly name: string;
  readonly description: string;
  readonly aliases: readonly string[];
  /** Key "" holds a command without subcommands. */
  readonly leaves: ReadonlyMap<string, Leaf>;
  /** Subcommand used in prefix mode when the first word is not a subcommand name. */
  readonly defaultSubcommand: string | undefined;
}

const toLeaf = <TOptions extends OptionsShape>(definition: LeafDefinition<TOptions>): Leaf => ({
  ...definition,
  options: definition.options ?? {},
  aliases: definition.aliases ?? [],
  cooldown: definition.cooldown,
  run: definition.run as Leaf["run"],
});

/** Defines a subcommand for `defineCommand({ subcommands })`. */
export const subcommand = <TOptions extends OptionsShape = Record<string, never>>(
  definition: LeafDefinition<TOptions>,
): Leaf => toLeaf(definition);

interface Base extends Access {
  name: string;
  description: string;
  /** Extra prefix names for the command itself. */
  aliases?: readonly string[];
}

type CommandDefinition<TOptions extends OptionsShape> =
  | (Base & Omit<LeafDefinition<TOptions>, "description" | "aliases">)
  | (Base & { subcommands: Record<string, Leaf>; defaultSubcommand?: string });

/**
 * Defines a command once for both slash and prefix use.
 *
 * Use `run` for a single command, or `subcommands` with `subcommand()` entries.
 */
export function defineCommand<TOptions extends OptionsShape = Record<string, never>>(
  definition: CommandDefinition<TOptions>,
): Command {
  const access: Access = {
    ...(definition.permissions === undefined ? {} : { permissions: definition.permissions }),
    ...(definition.ownerOnly === undefined ? {} : { ownerOnly: definition.ownerOnly }),
  };
  const base = {
    ...access,
    name: definition.name,
    description: definition.description,
    aliases: definition.aliases ?? [],
  };
  if ("subcommands" in definition) {
    return {
      ...base,
      leaves: new Map(Object.entries(definition.subcommands)),
      defaultSubcommand: definition.defaultSubcommand,
    };
  }
  const leaf = toLeaf({ ...definition, description: definition.description, aliases: [] });
  return { ...base, leaves: new Map([["", leaf]]), defaultSubcommand: undefined };
}

/**
 * Prefix aliases of a subcommand. Every command alias also works with the subcommand name, so
 * with the alias "bday", "bday set" reaches "birthday set" without being listed.
 */
export function leafAliases(command: Command, name: string): string[] {
  const leaf = command.leaves.get(name);
  const derived = name === "" ? [] : command.aliases.map((alias) => `${alias} ${name}`);
  return [...new Set([...(leaf?.aliases ?? []), ...derived])];
}
