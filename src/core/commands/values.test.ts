import type { Guild } from "discord.js";
import { describe, expect, it } from "vitest";

import { opt } from "./options.ts";
import { ArgumentError, prefixValues, usage } from "./values.ts";

const guild = {} as Guild;

describe("prefixValues", () => {
  it("reads options in order", async () => {
    const options = { amount: opt.integer("Amount"), reason: opt.string("Reason").rest() };
    await expect(prefixValues("50 for being nice", guild, options)).resolves.toEqual({
      amount: 50,
      reason: "for being nice",
    });
  });

  it("skips an optional option that cannot read the next word", async () => {
    const options = {
      duration: opt.duration("Duration").optional(),
      reason: opt.string("Reason").rest().optional(),
    };
    await expect(prefixValues("being rude", guild, options)).resolves.toEqual({
      duration: undefined,
      reason: "being rude",
    });
    await expect(prefixValues("2h being rude", guild, options)).resolves.toEqual({
      duration: 7_200_000,
      reason: "being rude",
    });
  });

  it("keeps quoted words together", async () => {
    const options = { city: opt.string("City"), days: opt.integer("Days").optional() };
    await expect(prefixValues('"New York" 3', guild, options)).resolves.toEqual({
      city: "New York",
      days: 3,
    });
  });

  it("rejects missing, invalid and extra input", async () => {
    const options = { amount: opt.integer("Amount") };
    await expect(prefixValues("", guild, options)).rejects.toThrow(ArgumentError);
    await expect(prefixValues("lots", guild, options)).rejects.toThrow("not a valid number");
    await expect(prefixValues("5 6", guild, options)).rejects.toThrow("couldn't read `6`");
  });

  it("checks limits and choices", async () => {
    await expect(prefixValues("0", guild, { n: opt.integer("N").min(1) })).rejects.toThrow(
      "at least 1",
    );
    const choice = { kind: opt.string("Kind").choices([{ name: "Voice", value: "voice" }]) };
    await expect(prefixValues("text", guild, choice)).rejects.toThrow("must be one of `voice`");
  });
});

describe("strict input", () => {
  it("reads perm as an empty duration and consumes it", async () => {
    const options = {
      duration: opt.duration("Duration").optional(),
      reason: opt.string("Reason").rest().optional(),
    };
    await expect(prefixValues("perm being rude", guild, options)).resolves.toEqual({
      duration: undefined,
      reason: "being rude",
    });
  });

  it.each(["1e300", "0x10", "1.5", "99999999999999999999"])(
    "rejects %j as an integer",
    async (text) => {
      await expect(prefixValues(text, guild, { n: opt.integer("N") })).rejects.toThrow(
        ArgumentError,
      );
    },
  );

  it("accepts digit separators", async () => {
    await expect(prefixValues("1,000", guild, { n: opt.integer("N") })).resolves.toEqual({
      n: 1000,
    });
  });
});

describe("usage", () => {
  it("marks required and optional options", () => {
    const options = { job: opt.string("Job"), page: opt.integer("Page").optional() };
    expect(usage("-", "jobs buy", options)).toBe("-jobs buy <job> [page]");
  });
});
