import { describe, expect, it, vi } from "vitest";

import { countActions, listActions } from "#modules/moderation/actions.service.ts";
import { listTerms } from "#modules/moderation/blocked-terms.service.ts";
import { previousNickname } from "#modules/moderation/nicknames.service.ts";
import { useTestDb } from "#test/helpers/db.ts";

import { moderationImporter } from "./moderation.ts";

useTestDb();

const GUILD = "1211618366763044874";
const USER = "123456789012345678";

const files: Record<string, unknown> = {
  "warnings.json": {
    [GUILD]: { [USER]: [{ reason: "spam", timestamp: "2024-05-01T12:00:00.123456" }, { bad: 1 }] },
  },
  "user_actions.json": {
    [GUILD]: {
      [USER]: [
        { action: "mute", timestamp: "2024-05-02T12:00:00", reason: null, duration: "10m" },
        { action: "warn", timestamp: "2024-05-02T13:00:00", reason: "counted in warnings" },
        { action: "jail", timestamp: "2024-05-03T12:00:00", duration: "permanent" },
      ],
    },
  },
  "nickname_history.json": {
    [GUILD]: { [USER]: [{ old_nick: "Old", new_nick: "New", timestamp: "2024-05-04T12:00:00" }] },
  },
  "punishments.json": {
    [`${USER}_${GUILD}`]: [
      { type: "kick", reason: "Used blocked term: x", timestamp: "2024-05-05T12:00:00" },
    ],
    "not-a-key": [{ type: "ban", timestamp: "2024-05-05T12:00:00" }],
  },
  // Python wrote the guild ID as a number, so JSON.parse rounds it.
  "blockedterms.json": {
    badword: {
      punishment_type: "mute",
      duration: 600,
      custom_text: "No",
      advanced_filtering: true,
      // legacySource turns large numeric IDs into their exact text.
      guild_id: GUILD,
    },
    other: { punishment_type: "explode", guild_id: Number(GUILD) },
  },
};

describe("moderationImporter", () => {
  it("imports every file and skips malformed entries", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    const rows = moderationImporter.run({ read: (file) => files[file] });

    expect(rows).toBe(6);
    expect(warn).toHaveBeenCalledWith("moderation: skipped 3 malformed entries");
    const actions = listActions(GUILD, USER);
    expect(countActions(actions)).toEqual(
      new Map([
        ["kick", 1],
        ["jail", 1],
        ["mute", 1],
        ["warn", 1],
      ]),
    );
    expect(actions.find((a) => a.action === "mute")?.durationMs).toBe(600_000);
    expect(actions.find((a) => a.action === "warn")?.createdAt).toEqual(
      new Date("2024-05-01T12:00:00.123Z"),
    );
    expect(previousNickname(GUILD, USER)).toBe("Old");
    expect(listTerms(GUILD)).toEqual([
      expect.objectContaining({ term: "badword", durationMs: 600_000, advanced: true }),
    ]);
  });

  it("does nothing when no files exist", () => {
    expect(moderationImporter.run({ read: () => undefined })).toBe(0);
  });
});
