import { describe, expect, it } from "vitest";

import { defineCommand, subcommand } from "./define.ts";
import { commandHelp, findHelpTarget, leafHelp, stripHelpFlag } from "./help.ts";
import { opt } from "./options.ts";

const run = () => Promise.resolve();
const birthday = defineCommand({
  name: "birthday",
  description: "Birthdays",
  aliases: ["bday"],
  defaultSubcommand: "show",
  subcommands: {
    show: subcommand({ description: "Show a birthday", run }),
    set: subcommand({
      description: "Set your birthday",
      aliases: ["bday set"],
      options: { date: opt.string("Your birthday, e.g. 24.12") },
      run,
    }),
  },
});
const jobs = defineCommand({
  name: "jobs",
  description: "Jobs",
  subcommands: { buy: subcommand({ description: "Buy a job", aliases: ["buyjob"], run }) },
});
const balance = defineCommand({ name: "balance", description: "Balance", aliases: ["bal"], run });
const commands = [birthday, jobs, balance];

describe("stripHelpFlag", () => {
  it("removes a trailing --help or -help", () => {
    expect(stripHelpFlag("bday --help")).toBe("bday");
    expect(stripHelpFlag("bday set -HELP")).toBe("bday set");
    expect(stripHelpFlag("bday set 24.12")).toBeUndefined();
  });
});

describe("findHelpTarget", () => {
  it("finds a command with subcommands by name or alias", () => {
    expect(findHelpTarget(commands, "bday")).toMatchObject({ kind: "command", command: birthday });
    expect(findHelpTarget(commands, "birthday")).toMatchObject({ kind: "command" });
  });

  it("finds subcommands by path, two-word alias and one-word alias", () => {
    expect(findHelpTarget(commands, "birthday set")).toMatchObject({ kind: "leaf", name: "set" });
    expect(findHelpTarget(commands, "bday set")).toMatchObject({ kind: "leaf", name: "set" });
    expect(findHelpTarget(commands, "buyjob")).toMatchObject({ kind: "leaf", name: "buy" });
  });

  it("treats a command without subcommands as a leaf", () => {
    expect(findHelpTarget(commands, "bal")).toMatchObject({ kind: "leaf", name: "" });
    expect(findHelpTarget(commands, "nothing")).toBeUndefined();
  });
});

describe("help embeds", () => {
  const prefixes = { prefix: "-", textPrefix: "-" };

  it("shows the command, then each subcommand", () => {
    const text = commandHelp(birthday, prefixes).data.description ?? "";
    expect(text.indexOf("**Aliases**")).toBeGreaterThan(text.indexOf("**Subcommands**"));
    expect(text).toContain("`-birthday set <date>` Set your birthday");
    expect(text).toContain("**Default:** `-birthday` runs `show`");
    expect(text).toContain("**Aliases**\n`-bday` for `-birthday`");
    expect(text).not.toContain("`-bday set` for");
  });

  it("lists aliases that are not just the command alias plus the subcommand", () => {
    const text = commandHelp(jobs, prefixes).data.description ?? "";
    expect(text).toContain("`-buyjob` for `-jobs buy`");
  });

  it("shows a subcommand's usage and options", () => {
    const target = findHelpTarget(commands, "bday set");
    if (target?.kind !== "leaf") throw new Error("expected a subcommand");
    const text = leafHelp(target, prefixes).data.description ?? "";
    expect(text).toContain("**Usage:** `-birthday set <date>`");
    expect(text).toContain("`date` text, required. Your birthday, e.g. 24.12.");
    expect(text).toContain("**Aliases**\n`-bday set` for `-birthday set`");
  });
});
