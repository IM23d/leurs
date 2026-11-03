import { describe, expect, it } from "vitest";

import { useTestDb } from "#test/helpers/db.ts";

import { clearCooldown, takeCooldown } from "./cooldowns.ts";

useTestDb();

describe("takeCooldown", () => {
  it("blocks until a short cooldown ends", () => {
    expect(takeCooldown("short", "u1", 10, 0)).toBe(0);
    expect(takeCooldown("short", "u1", 10, 4000)).toBe(6000);
    expect(takeCooldown("short", "u1", 10, 10_000)).toBe(0);
  });

  it("stores long cooldowns in the database", () => {
    expect(takeCooldown("work", "u1", 86_400, 0)).toBe(0);
    expect(takeCooldown("work", "u1", 86_400, 1000)).toBe(86_399_000);
    clearCooldown("work", "u1");
    expect(takeCooldown("work", "u1", 86_400, 2000)).toBe(0);
  });
});
