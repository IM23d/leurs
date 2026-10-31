import type { Command, Leaf } from "./commands/define.ts";
import type { Component } from "./components.ts";
import type { ContextMenu } from "./context-menus.ts";
import type { EventHandler } from "./events.ts";
import type { Module } from "./module.ts";
import type { RunnableTask } from "./tasks/define-task.ts";

export interface Route {
  readonly command: Command;
  readonly leaf: Leaf;
  /** "jobs buy" for a subcommand, "balance" for a plain command. */
  readonly path: string;
}

/** Everything the modules provide, indexed for lookups. Built once at startup. */
export interface Registry {
  readonly commands: readonly Command[];
  readonly contextMenus: ReadonlyMap<string, ContextMenu>;
  readonly components: ReadonlyMap<string, Component>;
  readonly events: readonly EventHandler[];
  readonly tasks: readonly RunnableTask[];
  /** Prefix names and aliases, lowercased. Keys may contain one space. */
  readonly prefixRoutes: ReadonlyMap<string, Route>;
}

function uniqueMap<T>(entries: readonly (readonly [string, T])[], what: string): Map<string, T> {
  const map = new Map<string, T>();
  for (const [key, value] of entries) {
    if (map.has(key)) throw new Error(`Duplicate ${what}: "${key}"`);
    map.set(key, value);
  }
  return map;
}

function prefixEntries(command: Command): (readonly [string, Route])[] {
  return [...command.leaves].flatMap(([name, leaf]) => {
    const path = name === "" ? command.name : `${command.name} ${name}`;
    const route = { command, leaf, path };
    const isDefault = name === "" || name === command.defaultSubcommand;
    const names = [path, ...leaf.aliases, ...(isDefault ? [command.name, ...command.aliases] : [])];
    return [...new Set(names)].map((key) => [key.toLowerCase(), route] as const);
  });
}

export function buildRegistry(modules: readonly Module[]): Registry {
  const commands = modules.flatMap((module) => module.commands ?? []);
  uniqueMap(
    commands.map((command) => [command.name, command]),
    "command name",
  );
  return {
    commands,
    contextMenus: uniqueMap(
      modules.flatMap((m) => m.contextMenus ?? []).map((menu) => [menu.name, menu]),
      "context menu",
    ),
    components: uniqueMap(
      modules.flatMap((m) => m.components ?? []).map((component) => [component.id, component]),
      "component ID",
    ),
    events: modules.flatMap((m) => m.events ?? []),
    tasks: [
      ...uniqueMap(
        modules.flatMap((m) => m.tasks ?? []).map((task) => [task.kind, task]),
        "task kind",
      ).values(),
    ],
    prefixRoutes: uniqueMap(commands.flatMap(prefixEntries), "prefix name or alias"),
  };
}

/** Finds the route for prefix text. Tries a two-word name first, so "tz set" beats "tz". */
export function findPrefixRoute(
  registry: Registry,
  text: string,
): { route: Route; rest: string } | undefined {
  const words = text.trim().split(/\s+/);
  const candidates = [
    { key: words.slice(0, 2).join(" "), count: 2 },
    { key: words[0] ?? "", count: 1 },
  ].filter(({ count }) => words.length >= count);
  for (const { key, count } of candidates) {
    const route = registry.prefixRoutes.get(key.toLowerCase());
    if (route) return { route, rest: restOf(text, count) };
  }
  return undefined;
}

/** The original text after the first `count` words, with its spacing and quotes kept. */
function restOf(text: string, count: number): string {
  const padded = `${text.trim()} `;
  const match = new RegExp(String.raw`^(?:\S+\s+){${count}}`).exec(padded);
  return match ? padded.slice(match[0].length).trim() : "";
}
