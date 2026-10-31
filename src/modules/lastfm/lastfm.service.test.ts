import { describe, expect, it } from "vitest";

import { useTestDb } from "#test/helpers/db.ts";

import { allAccounts, getUsername, linkAccount, unlinkAccount } from "./lastfm.service.ts";

describe("lastfm accounts", () => {
  useTestDb();

  it("links, relinks and unlinks an account", () => {
    linkAccount("1", "first");
    linkAccount("1", "second");
    expect(getUsername("1")).toBe("second");
    expect(unlinkAccount("1")).toBe(true);
    expect(getUsername("1")).toBeUndefined();
    expect(unlinkAccount("1")).toBe(false);
  });

  it("lists every account by username", () => {
    linkAccount("1", "zed");
    linkAccount("2", "amy");
    expect(allAccounts().map((account) => account.username)).toEqual(["amy", "zed"]);
  });
});
