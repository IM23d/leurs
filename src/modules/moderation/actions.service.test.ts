import { describe, expect, it } from "vitest";

import { UserError } from "#core/errors.ts";
import { useTestDb } from "#test/helpers/db.ts";

import {
  checkTimeoutDuration,
  countActions,
  listActions,
  MAX_TIMEOUT_MS,
  recordAction,
} from "./actions.service.ts";

useTestDb();

const base = { guildId: "g1", userId: "u1", moderatorId: "m1" } as const;

describe("mod actions", () => {
  it("lists a member's actions newest first, per server", () => {
    recordAction({ ...base, action: "warn", reason: "spam" }, new Date(1000));
    recordAction({ ...base, action: "mute", durationMs: 60_000 }, new Date(3000));
    recordAction({ ...base, action: "warn" }, new Date(2000));
    recordAction({ ...base, guildId: "g2", action: "ban" }, new Date(4000));

    const actions = listActions("g1", "u1");
    expect(actions.map((a) => a.action)).toEqual(["mute", "warn", "warn"]);
    expect(actions[0]).toMatchObject({ durationMs: 60_000, reason: null, moderatorId: "m1" });
    expect(actions[2]).toMatchObject({ reason: "spam", durationMs: null });
  });

  it("counts actions by type", () => {
    recordAction({ ...base, action: "warn" });
    recordAction({ ...base, action: "kick" });
    recordAction({ ...base, action: "warn" });
    expect(countActions(listActions("g1", "u1"))).toEqual(
      new Map([
        ["warn", 2],
        ["kick", 1],
      ]),
    );
  });

  it("records automod actions without a moderator", () => {
    recordAction({ ...base, moderatorId: null, action: "kick" });
    expect(listActions("g1", "u1")[0]?.moderatorId).toBeNull();
  });
});

describe("checkTimeoutDuration", () => {
  it("allows up to 28 days", () => {
    expect(() => {
      checkTimeoutDuration(MAX_TIMEOUT_MS);
    }).not.toThrow();
  });

  it("rejects longer durations", () => {
    expect(() => {
      checkTimeoutDuration(MAX_TIMEOUT_MS + 1);
    }).toThrow(UserError);
  });
});
