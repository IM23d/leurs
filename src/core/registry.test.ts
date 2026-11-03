import { describe, expect, it } from "vitest";

import { defineCommand, subcommand } from "./commands/define.ts";
import { defineModule } from "./module.ts";
import { buildRegistry, findPrefixRoute } from "./registry.ts";

const run = () => Promise.resolve();
const jobs = defineCommand({
  name: "jobs",
  description: "Jobs",
  defaultSubcommand: "list",
  subcommands: {
    list: subcommand({ description: "List", run }),
    buy: subcommand({ description: "Buy", aliases: ["buyjob"], run }),
  },
});
const tz = defineCommand({ name: "time", description: "Time", aliases: ["tz"], run });
const timezone = defineCommand({
  name: "timezone",
  description: "Timezone",
  subcommands: { set: subcommand({ description: "Set", aliases: ["tz set"], run }) },
});
const registry = buildRegistry([defineModule({ name: "test", commands: [jobs, tz, timezone] })]);

describe("findPrefixRoute", () => {
  it("finds subcommands, aliases and defaults", () => {
    expect(findPrefixRoute(registry, "jobs buy Artist")).toMatchObject({
      route: { path: "jobs buy" },
      rest: "Artist",
    });
    expect(findPrefixRoute(registry, "BUYJOB  Stock Trader")).toMatchObject({
      route: { path: "jobs buy" },
      rest: "Stock Trader",
    });
    expect(findPrefixRoute(registry, "jobs 2")).toMatchObject({ route: { path: "jobs list" } });
  });

  it("prefers a two-word alias", () => {
    expect(findPrefixRoute(registry, "tz set Europe/Zurich")).toMatchObject({
      route: { path: "timezone set" },
      rest: "Europe/Zurich",
    });
    expect(findPrefixRoute(registry, "tz @someone")).toMatchObject({ route: { path: "time" } });
  });

  it("ignores unknown commands", () => {
    expect(findPrefixRoute(registry, "nothing here")).toBeUndefined();
  });
});

it("rejects duplicate prefix names", () => {
  const clash = defineCommand({ name: "buyjob", description: "Clash", run });
  expect(() => buildRegistry([defineModule({ name: "x", commands: [jobs, clash] })])).toThrow(
    'Duplicate prefix name or alias: "buyjob"',
  );
});
