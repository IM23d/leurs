import { describe, expect, it } from "vitest";

import { findReactionRole, listReactionRoles } from "#modules/roles/reaction-roles.service.ts";
import { backupStatus, getBackup } from "#modules/roles/role-backups.service.ts";
import { useTestDb } from "#test/helpers/db.ts";

import { rolesImporter } from "./roles.ts";
import type { LegacySource } from "./source.ts";

useTestDb();

const guild = "100000000000000001";
const member = "200000000000000002";
const role = "300000000000000003";
const message = "400000000000000004";

const sourceOf = (files: Record<string, unknown>): LegacySource => ({
  read: (file) => files[file],
});

describe("rolesImporter", () => {
  it("imports backups and reaction roles and skips malformed entries", () => {
    const rows = rolesImporter.run(
      sourceOf({
        "saved_roles.json": {
          [guild]: {
            [member]: [role],
            "200000000000000005": [],
            bad: [role],
            "200000000000000006": [1.5e18],
          },
        },
        "roles_info.json": { last_save: "2025-01-02T03:04:05.123456", next_save: null },
        "reaction_roles.json": {
          [guild]: { [message]: { "👍": role, "<:pog:500000000000000005>": role, nope: role } },
        },
      }),
    );
    expect(rows).toBe(3);
    expect(getBackup(guild, member)).toEqual([role]);
    expect(backupStatus(guild).lastUpdate).toEqual(new Date("2025-01-02T03:04:05.123Z"));
    expect(findReactionRole(guild, message, "500000000000000005")?.emoji).toBe(
      "<:pog:500000000000000005>",
    );
    expect(listReactionRoles(guild)).toHaveLength(2);
  });

  it("imports nothing when the files are missing", () => {
    expect(rolesImporter.run(sourceOf({}))).toBe(0);
  });
});
