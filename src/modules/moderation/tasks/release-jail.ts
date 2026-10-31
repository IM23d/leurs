import { z } from "zod";

import { defineTask } from "#core/tasks/define-task.ts";
import { removeFromBackup } from "#modules/roles/api.ts";

import { logModAction } from "../mod-log.ts";

const payload = z.object({ guildId: z.string(), userId: z.string(), roleId: z.string() });

/** Takes the jail role away when a timed jail ends. */
export const releaseJailTask = defineTask({
  kind: "moderation.release-jail",
  payload,
  run: async ({ guildId, userId, roleId }, client) => {
    const guild = client.guilds.cache.get(guildId);
    if (!guild) return;
    const member = await guild.members.fetch(userId).catch(() => undefined);
    if (!member) {
      // The roles module restores backed up roles on rejoin, which would bring the jail role back.
      removeFromBackup(guildId, userId, roleId);
      return;
    }
    if (!member.roles.cache.has(roleId)) return;
    await member.roles.remove(roleId, "Jail time is over");
    await logModAction(guild, {
      title: "Unjail",
      target: member.user,
      moderator: client.user,
      reason: "Jail time is over",
    });
  },
});

/** Cancels a pending release, so a new jail or a manual unjail is not undone by an old timer. */
export function cancelJailRelease(guildId: string, userId: string): void {
  releaseJailTask
    .pending()
    .filter((task) => task.payload.guildId === guildId && task.payload.userId === userId)
    .forEach((task) => releaseJailTask.cancel(task.id));
}
