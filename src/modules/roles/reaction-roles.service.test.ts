import { describe, expect, it } from "vitest";

import { useTestDb } from "#test/helpers/db.ts";

import {
  addReactionRole,
  findReactionRole,
  listReactionRoles,
  removeReactionRole,
} from "./reaction-roles.service.ts";

useTestDb();

const link = { guildId: "g1", channelId: "c1", messageId: "m1", emojiKey: "👍", emoji: "👍" };

describe("reaction roles", () => {
  it("finds a link by server, message and emoji", () => {
    addReactionRole({ ...link, roleId: "r1" });
    expect(findReactionRole("g1", "m1", "👍")?.roleId).toBe("r1");
    expect(findReactionRole("g2", "m1", "👍")).toBeUndefined();
    expect(findReactionRole("g1", "m1", "👎")).toBeUndefined();
  });

  it("replaces the role of an emoji that is already linked", () => {
    addReactionRole({ ...link, roleId: "r1" });
    addReactionRole({ ...link, roleId: "r2" });
    expect(listReactionRoles("g1").map(({ roleId }) => roleId)).toEqual(["r2"]);
  });

  it("removes a link and reports a missing one", () => {
    addReactionRole({ ...link, roleId: "r1" });
    addReactionRole({ ...link, emojiKey: "123", emoji: "<:pog:123>", roleId: "r2" });
    expect(removeReactionRole("g1", "m1", "👍")?.roleId).toBe("r1");
    expect(removeReactionRole("g1", "m1", "👍")).toBeUndefined();
    expect(listReactionRoles("g1").map(({ roleId }) => roleId)).toEqual(["r2"]);
  });
});
