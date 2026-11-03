import {
  ApplicationCommandOptionType,
  ApplicationCommandType,
  InteractionContextType,
  PermissionFlagsBits,
  type RESTPostAPIApplicationCommandsJSONBody,
} from "discord.js";

import type { ContextMenu } from "../context-menus.ts";

import type { Command, Leaf } from "./define.ts";
import type { AnyOption } from "./options.ts";

function optionJson(name: string, option: AnyOption) {
  const { type, description, min, max, choices, autocomplete } = option.spec;
  const isText = type === ApplicationCommandOptionType.String;
  return {
    type,
    name,
    description,
    required: option.required,
    ...(choices ? { choices } : {}),
    ...(autocomplete ? { autocomplete: true } : {}),
    ...(min === undefined ? {} : isText ? { min_length: min } : { min_value: min }),
    ...(max === undefined ? {} : isText ? { max_length: max } : { max_value: max }),
  };
}

// Discord requires required options to come before optional ones.
const optionsJson = (leaf: Leaf) =>
  Object.entries(leaf.options)
    .map(([name, option]) => optionJson(name, option))
    .toSorted((a, b) => Number(b.required) - Number(a.required));

const memberPermissions = (permissions: bigint | undefined, ownerOnly: boolean | undefined) => {
  const required = ownerOnly ? PermissionFlagsBits.Administrator : permissions;
  return required === undefined ? {} : { default_member_permissions: required.toString() };
};

export function commandJson(command: Command): RESTPostAPIApplicationCommandsJSONBody {
  const single = command.leaves.get("");
  const options = single
    ? optionsJson(single)
    : [...command.leaves].map(([name, leaf]) => ({
        type: ApplicationCommandOptionType.Subcommand,
        name,
        description: leaf.description,
        options: optionsJson(leaf),
      }));
  return {
    type: ApplicationCommandType.ChatInput,
    name: command.name,
    description: command.description,
    options,
    contexts: [InteractionContextType.Guild],
    ...memberPermissions(command.permissions, command.ownerOnly),
  } as RESTPostAPIApplicationCommandsJSONBody;
}

export function contextMenuJson(menu: ContextMenu): RESTPostAPIApplicationCommandsJSONBody {
  return {
    type: menu.type === "message" ? ApplicationCommandType.Message : ApplicationCommandType.User,
    name: menu.name,
    contexts: [InteractionContextType.Guild],
    ...memberPermissions(menu.permissions, undefined),
  };
}
