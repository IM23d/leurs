import type { ChatInputCommandInteraction, Guild } from "discord.js";

import { UserError } from "../errors.ts";

import type { AnyOption, OptionSpec, OptionsShape } from "./options.ts";
import { tokenize } from "./tokenize.ts";

/** Bad or missing arguments. The dispatcher adds the command's usage line. */
export class ArgumentError extends UserError {
  override name = "ArgumentError";
}

function checkLimits(name: string, spec: OptionSpec<unknown>, value: unknown): void {
  const { min, max, choices } = spec;
  if (choices && !choices.some((choice) => choice.value === value)) {
    const allowed = choices.map((choice) => `\`${String(choice.value)}\``).join(", ");
    throw new ArgumentError(`\`${name}\` must be one of ${allowed}.`);
  }
  const size =
    typeof value === "number" ? value : typeof value === "string" ? value.length : undefined;
  if (size === undefined) return;
  const unit = typeof value === "string" ? " characters" : "";
  if (min !== undefined && size < min) {
    throw new ArgumentError(`\`${name}\` must be at least ${min}${unit}.`);
  }
  if (max !== undefined && size > max) {
    throw new ArgumentError(`\`${name}\` must be at most ${max}${unit}.`);
  }
}

function finish(name: string, option: AnyOption, value: unknown): unknown {
  if (value === undefined) {
    if (option.required) throw new ArgumentError(`\`${name}\` is missing.`);
    return undefined;
  }
  checkLimits(name, option.spec, value);
  return value;
}

export async function slashValues(
  interaction: ChatInputCommandInteraction,
  options: OptionsShape,
): Promise<Record<string, unknown>> {
  const entries = await Promise.all(
    Object.entries(options).map(async ([name, option]) => {
      const value = await option.spec.fromSlash(interaction, name);
      if (value === undefined && interaction.options.get(name) !== null) {
        throw new ArgumentError(`\`${name}\` is not a valid ${option.spec.placeholder}.`);
      }
      return [name, finish(name, option, value)] as const;
    }),
  );
  return Object.fromEntries(entries);
}

/**
 * Reads options from prefix text in order. An optional option that cannot read the next word is
 * skipped, so `-jail @user being rude` works without a duration.
 */
export async function prefixValues(
  text: string,
  guild: Guild,
  options: OptionsShape,
): Promise<Record<string, unknown>> {
  const tokens = tokenize(text);
  const values: Record<string, unknown> = {};
  let index = 0;
  for (const [name, option] of Object.entries(options)) {
    const token = tokens[index];
    let value: unknown;
    if (token && option.spec.rest) {
      value = await option.spec.fromText(text.slice(token.start).trim(), guild);
      index = tokens.length;
    } else if (token) {
      value = await option.spec.fromText(token.value, guild);
      if (value !== undefined) index += 1;
      else if (option.required) {
        throw new ArgumentError(`\`${token.value}\` is not a valid ${option.spec.placeholder}.`);
      }
    }
    values[name] = finish(name, option, value);
  }
  const leftover = tokens[index];
  if (leftover) throw new ArgumentError(`I couldn't read \`${leftover.value}\`.`);
  return values;
}

/** For example "-jobs buy <job> [page]". */
export function usage(prefix: string, path: string, options: OptionsShape): string {
  const parts = Object.entries(options).map(([name, option]) =>
    option.required ? `<${name}>` : `[${name}]`,
  );
  return [`${prefix}${path}`, ...parts].join(" ");
}
