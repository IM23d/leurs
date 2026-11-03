import { describe, expect, it } from "vitest";

import { useTestDb } from "#test/helpers/db.ts";

import { previousNickname, recordNicknameChange } from "./nicknames.service.ts";

useTestDb();

describe("nickname history", () => {
  it("has no previous nickname without history", () => {
    expect(previousNickname("g1", "u1")).toBeUndefined();
  });

  it("returns the nickname before the latest change", () => {
    recordNicknameChange("g1", "u1", null, "First", new Date(1000));
    recordNicknameChange("g1", "u1", "First", "Second", new Date(2000));
    expect(previousNickname("g1", "u1")).toBe("First");
    expect(previousNickname("g2", "u1")).toBeUndefined();
  });

  it("returns null when the member had no nickname before", () => {
    recordNicknameChange("g1", "u1", null, "First");
    expect(previousNickname("g1", "u1")).toBeNull();
  });

  it("swaps back and forth when reverting twice", () => {
    recordNicknameChange("g1", "u1", "Old", "New", new Date(1000));
    recordNicknameChange("g1", "u1", "New", "Old", new Date(2000));
    expect(previousNickname("g1", "u1")).toBe("New");
  });
});
