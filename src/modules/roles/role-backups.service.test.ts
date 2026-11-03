import { describe, expect, it } from "vitest";

import { useTestDb } from "#test/helpers/db.ts";

import {
  backupStatus,
  getBackup,
  removeFromBackup,
  saveBackup,
  saveBackups,
} from "./role-backups.service.ts";

useTestDb();

describe("role backups", () => {
  it("replaces a member's backup and keeps servers apart", () => {
    saveBackup("g1", { userId: "u1", roleIds: ["r1", "r2"] });
    saveBackup("g1", { userId: "u1", roleIds: ["r3"] });
    saveBackup("g2", { userId: "u1", roleIds: ["r9"] });
    expect(getBackup("g1", "u1")).toEqual(["r3"]);
    expect(getBackup("g2", "u1")).toEqual(["r9"]);
  });

  it("drops the backup of a member without roles", () => {
    saveBackup("g1", { userId: "u1", roleIds: ["r1"] });
    saveBackup("g1", { userId: "u1", roleIds: [] });
    expect(getBackup("g1", "u1")).toEqual([]);
    expect(backupStatus("g1").members).toBe(0);
  });

  it("removes one role from a backup", () => {
    saveBackup("g1", { userId: "u1", roleIds: ["r1", "r2"] });
    removeFromBackup("g1", "u1", "r1");
    expect(getBackup("g1", "u1")).toEqual(["r2"]);
    removeFromBackup("g1", "u1", "r2");
    expect(backupStatus("g1").members).toBe(0);
  });

  it("saves many members and reports the latest change", () => {
    const at = new Date("2025-01-02T03:04:05Z");
    const saved = saveBackups(
      "g1",
      [
        { userId: "u1", roleIds: ["r1"] },
        { userId: "u2", roleIds: [] },
        { userId: "u3", roleIds: ["r1", "r2"] },
      ],
      at,
    );
    expect(saved).toBe(2);
    expect(backupStatus("g1")).toEqual({ members: 2, lastUpdate: at });
    expect(backupStatus("g2")).toEqual({ members: 0, lastUpdate: undefined });
  });
});
