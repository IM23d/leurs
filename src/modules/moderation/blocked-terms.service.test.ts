import { beforeEach, describe, expect, it } from "vitest";

import { UserError } from "#core/errors.ts";
import { useTestDb } from "#test/helpers/db.ts";

import {
  blockTerm,
  clearTermCache,
  findBlockedTerm,
  listTerms,
  matchTerm,
  normalizeText,
  unblockTerm,
} from "./blocked-terms.service.ts";
import type { BlockedTerm } from "./moderation.schema.ts";

useTestDb();
beforeEach(clearTermCache);

const input = {
  guildId: "g1",
  term: "badword",
  punishment: "warn",
  durationMs: undefined,
  customText: undefined,
  advanced: false,
  addedById: "m1",
} as const;

const term = (text: string, advanced: boolean): BlockedTerm => ({
  id: 1,
  guildId: "g1",
  term: text,
  punishment: "warn",
  durationMs: null,
  customText: null,
  advanced,
  addedById: null,
  createdAt: new Date(0),
});

describe("normalizeText", () => {
  it("strips accents, digits, symbols and long runs of a letter", () => {
    expect(normalizeText("Hééééllo!!! W0rld   1234")).toBe("hello wrld");
    expect(normalizeText("b.a.d-w_o_r_d")).toBe("badw_o_r_d");
  });

  it("keeps doubled letters, like the old bot", () => {
    expect(normalizeText("Hello")).toBe("hello");
    expect(normalizeText("heeeey")).toBe("hey");
  });
});

describe("matchTerm", () => {
  it("matches basic terms case-insensitively as substrings", () => {
    expect(matchTerm("That is a BadWord!", [term("badword", false)])).toBeDefined();
    expect(matchTerm("b@dword", [term("badword", false)])).toBeUndefined();
  });

  it("matches advanced terms after normalizing both sides", () => {
    const advanced = term("badword", true);
    expect(matchTerm("bád.wörd", [advanced])).toBeDefined();
    expect(matchTerm("bad1word", [advanced])).toBeDefined();
    expect(matchTerm("baaaadword", [advanced])).toBeDefined();
    expect(matchTerm("B-A-D-W-O-R-D", [advanced])).toBeDefined();
    expect(matchTerm("bad word", [advanced])).toBeUndefined();
  });

  it("returns the first term that matches", () => {
    const first = { ...term("one", false), id: 1 };
    const second = { ...term("two", false), id: 2 };
    expect(matchTerm("two and one", [first, second])).toBe(first);
  });
});

describe("blocked terms", () => {
  it("adds, finds and removes a term per server", () => {
    blockTerm(input);
    expect(findBlockedTerm("g1", "this has BADWORD in it")?.term).toBe("badword");
    expect(findBlockedTerm("g2", "this has badword in it")).toBeUndefined();
    expect(unblockTerm("g1", "badword")).toBe(true);
    expect(findBlockedTerm("g1", "badword")).toBeUndefined();
    expect(unblockTerm("g1", "badword")).toBe(false);
  });

  it("replaces the settings when a term is blocked again", () => {
    blockTerm(input);
    blockTerm({ ...input, punishment: "ban", durationMs: 60_000, customText: "Bye" });
    expect(listTerms("g1")).toEqual([
      expect.objectContaining({ punishment: "ban", durationMs: 60_000, customText: "Bye" }),
    ]);
  });

  it("needs a duration of at most 28 days for mutes", () => {
    expect(() => blockTerm({ ...input, punishment: "mute" })).toThrow(UserError);
    expect(() => blockTerm({ ...input, punishment: "mute", durationMs: 29 * 86_400_000 })).toThrow(
      UserError,
    );
    expect(blockTerm({ ...input, punishment: "mute", durationMs: 600_000 }).durationMs).toBe(
      600_000,
    );
  });

  it("allows durations only for mutes and bans", () => {
    expect(() => blockTerm({ ...input, punishment: "kick", durationMs: 1000 })).toThrow(UserError);
    expect(blockTerm({ ...input, punishment: "ban" }).durationMs).toBeNull();
  });

  it("rejects an empty term", () => {
    expect(() => blockTerm({ ...input, term: "   " })).toThrow(UserError);
  });
});
