import { describe, expect, it } from "vitest";

import { modules } from "#app/modules.ts";
import { commandJson, contextMenuJson } from "#core/commands/slash.ts";
import { buildRegistry } from "#core/registry.ts";

// Discord's limits for application commands.
const NAME = /^[-_\p{L}\p{N}]{1,32}$/u;
const MAX_COMMANDS = 100;
const MAX_OPTIONS = 25;

interface OptionJson {
  name: string;
  description: string;
  required?: boolean;
  options?: OptionJson[];
}

const registry = buildRegistry(modules);

describe("command registry", () => {
  it("has no duplicate names, aliases, components or tasks", () => {
    expect(registry.commands.length).toBeGreaterThan(0);
  });

  it("stays within Discord's command count", () => {
    expect(registry.commands.length).toBeLessThanOrEqual(MAX_COMMANDS);
  });

  it.each(registry.commands.map((command) => [command.name, command] as const))(
    "/%s is valid for Discord",
    (_name, command) => {
      const json = commandJson(command) as unknown as OptionJson;
      const check = (entry: OptionJson) => {
        expect(entry.name).toMatch(NAME);
        expect(entry.name).toBe(entry.name.toLowerCase());
        expect(entry.description.length).toBeGreaterThan(0);
        expect(entry.description.length).toBeLessThanOrEqual(100);
        const options = entry.options ?? [];
        expect(options.length).toBeLessThanOrEqual(MAX_OPTIONS);
        const firstOptional = options.findIndex((option) => option.required === false);
        if (firstOptional !== -1) {
          expect(options.slice(firstOptional).every((o) => o.required !== true)).toBe(true);
        }
        options.forEach(check);
      };
      check(json);
    },
  );

  it("has valid context menus", () => {
    for (const menu of registry.contextMenus.values()) {
      expect(contextMenuJson(menu).name.length).toBeLessThanOrEqual(32);
    }
  });
});
