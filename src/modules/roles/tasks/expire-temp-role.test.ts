import { describe, expect, it } from "vitest";

import { useTestDb } from "#test/helpers/db.ts";

import { cancelExpiry, expireTempRole, scheduleExpiry } from "./expire-temp-role.ts";

useTestDb();

const grant = { guildId: "g1", userId: "u1", roleId: "r1", channelId: "c1" };

describe("temporary role expiry", () => {
  it("replaces an earlier expiry of the same role", () => {
    scheduleExpiry(grant, new Date(1000));
    scheduleExpiry(grant, new Date(2000));
    scheduleExpiry({ ...grant, roleId: "r2" }, new Date(3000));
    expect(
      expireTempRole.pending().map(({ runAt, payload }) => [runAt.getTime(), payload.roleId]),
    ).toEqual([
      [2000, "r1"],
      [3000, "r2"],
    ]);
  });

  it("cancels only the matching member and role", () => {
    scheduleExpiry(grant, new Date(1000));
    scheduleExpiry({ ...grant, userId: "u2" }, new Date(1000));
    expect(cancelExpiry(grant)).toBe(1);
    expect(cancelExpiry(grant)).toBe(0);
    expect(expireTempRole.pending().map(({ payload }) => payload.userId)).toEqual(["u2"]);
  });
});
