import {
  ApplicationCommandOptionType,
  type APIApplicationCommandOptionChoice,
  type ChatInputCommandInteraction,
  type Guild,
  type GuildBasedChannel,
  type GuildMember,
  type Role,
  type User,
} from "discord.js";

import { isPermanent, parseDuration } from "#shared/lib/duration.ts";

import { resolveChannel, resolveMember, resolveRole } from "./resolve.ts";

export interface AutocompleteChoice {
  name: string;
  value: string;
}
export type AutocompleteHandler = (
  query: string,
  context: { guildId: string; userId: string },
) => AutocompleteChoice[] | Promise<AutocompleteChoice[]>;

/** Everything the framework needs to read one option from a slash command or a prefix message. */
export interface OptionSpec<TValue> {
  readonly type: ApplicationCommandOptionType;
  readonly description: string;
  readonly placeholder: string;
  readonly rest: boolean;
  /** Number range for numbers, length range for text. Checked in both modes. */
  readonly min: number | undefined;
  readonly max: number | undefined;
  readonly choices: readonly APIApplicationCommandOptionChoice[] | undefined;
  readonly autocomplete: AutocompleteHandler | undefined;
  /** Returns undefined when the option was not given. */
  fromSlash(interaction: ChatInputCommandInteraction, name: string): Promise<TValue | undefined>;
  /** Returns undefined when the text is not a valid value. */
  fromText(text: string, guild: Guild): Promise<TValue | undefined>;
}

/**
 * An immutable option definition. Each method returns a new option, so definitions chain:
 * `opt.string("Reason").rest().optional()`.
 */
export class Option<TValue, TRequired extends boolean = true> {
  readonly spec: OptionSpec<TValue>;
  readonly required: TRequired;

  constructor(spec: OptionSpec<TValue>, required: TRequired) {
    this.spec = spec;
    this.required = required;
  }

  optional(): Option<TValue, false> {
    return new Option(this.spec, false);
  }

  /** In prefix mode, takes the rest of the message as this option's text. */
  rest(): Option<TValue, TRequired> {
    return this.with({ rest: true });
  }

  min(min: number): Option<TValue, TRequired> {
    return this.with({ min });
  }

  max(max: number): Option<TValue, TRequired> {
    return this.with({ max });
  }

  choices(choices: readonly APIApplicationCommandOptionChoice[]): Option<TValue, TRequired> {
    return this.with({ choices });
  }

  autocomplete(autocomplete: AutocompleteHandler): Option<TValue, TRequired> {
    return this.with({ autocomplete });
  }

  private with(changes: Partial<OptionSpec<TValue>>): Option<TValue, TRequired> {
    return new Option({ ...this.spec, ...changes }, this.required);
  }
}

export type AnyOption = Option<unknown, boolean>;
export type OptionsShape = Record<string, AnyOption>;
export type OptionValues<TOptions extends OptionsShape> = {
  [K in keyof TOptions]: TOptions[K] extends Option<infer V, infer R>
    ? R extends true
      ? V
      : V | undefined
    : never;
};

function option<TValue>(
  type: ApplicationCommandOptionType,
  description: string,
  placeholder: string,
  read: Pick<OptionSpec<TValue>, "fromSlash" | "fromText">,
): Option<TValue> {
  return new Option<TValue, true>(
    {
      type,
      description,
      placeholder,
      rest: false,
      min: undefined,
      max: undefined,
      choices: undefined,
      autocomplete: undefined,
      ...read,
    },
    true,
  );
}

const nonNull = <T>(value: T | null | undefined): T | undefined => value ?? undefined;

function parseNumber(text: string, integer: boolean): number | undefined {
  const value = Number(text.replaceAll(/[,_']/g, ""));
  return !Number.isFinite(value) || (integer && !Number.isInteger(value)) ? undefined : value;
}

const BOOLEANS: Record<string, boolean> = {
  yes: true,
  true: true,
  on: true,
  no: false,
  false: false,
  off: false,
};

export const opt = {
  string: (description: string) =>
    option<string>(ApplicationCommandOptionType.String, description, "text", {
      fromSlash: (i, name) => Promise.resolve(nonNull(i.options.getString(name))),
      fromText: (text) => Promise.resolve(text === "" ? undefined : text),
    }),

  integer: (description: string) =>
    option<number>(ApplicationCommandOptionType.Integer, description, "number", {
      fromSlash: (i, name) => Promise.resolve(nonNull(i.options.getInteger(name))),
      fromText: (text) => Promise.resolve(parseNumber(text, true)),
    }),

  number: (description: string) =>
    option<number>(ApplicationCommandOptionType.Number, description, "number", {
      fromSlash: (i, name) => Promise.resolve(nonNull(i.options.getNumber(name))),
      fromText: (text) => Promise.resolve(parseNumber(text, false)),
    }),

  boolean: (description: string) =>
    option<boolean>(ApplicationCommandOptionType.Boolean, description, "yes|no", {
      fromSlash: (i, name) => Promise.resolve(nonNull(i.options.getBoolean(name))),
      fromText: (text) => Promise.resolve(BOOLEANS[text.toLowerCase()]),
    }),

  user: (description: string) =>
    option<User>(ApplicationCommandOptionType.User, description, "user", {
      fromSlash: (i, name) => Promise.resolve(nonNull(i.options.getUser(name))),
      fromText: async (text, guild) => (await resolveMember(guild, text))?.user,
    }),

  member: (description: string) =>
    option<GuildMember>(ApplicationCommandOptionType.User, description, "member", {
      fromSlash: (i, name) => {
        const member = i.options.getMember(name);
        return Promise.resolve(member && "guild" in member ? member : undefined);
      },
      fromText: (text, guild) => resolveMember(guild, text),
    }),

  role: (description: string) =>
    option<Role>(ApplicationCommandOptionType.Role, description, "role", {
      fromSlash: (i, name) => {
        const role = i.options.getRole(name);
        return Promise.resolve(role && "guild" in role ? role : undefined);
      },
      fromText: (text, guild) => Promise.resolve(resolveRole(guild, text)),
    }),

  channel: (description: string) =>
    option<GuildBasedChannel>(ApplicationCommandOptionType.Channel, description, "channel", {
      fromSlash: (i, name) => {
        const channel = i.options.getChannel(name);
        return Promise.resolve(channel && "guild" in channel ? channel : undefined);
      },
      fromText: (text, guild) => Promise.resolve(resolveChannel(guild, text)),
    }),

  /** Text read by `parse`. Return undefined from `parse` to reject the input. */
  custom: <TValue>(
    description: string,
    placeholder: string,
    parse: (text: string) => TValue | undefined,
  ) =>
    option<TValue>(ApplicationCommandOptionType.String, description, placeholder, {
      fromSlash: (i, name) => {
        const text = i.options.getString(name);
        return Promise.resolve(text === null ? undefined : parse(text));
      },
      fromText: (text) => Promise.resolve(parse(text)),
    }),

  /**
   * A duration such as "30m" or "2d", in milliseconds. "perm" and "permanent" read as no value,
   * so make the option optional when permanent is allowed.
   */
  duration: (description: string) =>
    option<number>(ApplicationCommandOptionType.String, description, "duration", {
      fromSlash: (i, name) => {
        const text = i.options.getString(name);
        return Promise.resolve(
          text === null || isPermanent(text) ? undefined : parseDuration(text),
        );
      },
      fromText: (text) => Promise.resolve(parseDuration(text)),
    }),
};
