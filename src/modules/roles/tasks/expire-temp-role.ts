import { z } from "zod";

import { defineTask } from "#core/tasks/define-task.ts";
import { embed } from "#shared/ui/embeds.ts";

import { removeFromBackup } from "../role-backups.service.ts";

const tempRole = z.object({
  guildId: z.string(),
  userId: z.string(),
  roleId: z.string(),
  /** Where the role was given. The expiry notice goes there. */
  channelId: z.string(),
});
export type TempRole = z.infer<typeof tempRole>;

export const expireTempRole = defineTask({
  kind: "roles.expire-temp-role",
  payload: tempRole,
  run: async ({ guildId, userId, roleId, channelId }, client) => {
    const guild = client.guilds.cache.get(guildId);
    if (!guild) return;
    const member = await guild.members.fetch(userId).catch(() => undefined);
    if (!member) {
      removeFromBackup(guildId, userId, roleId);
      return;
    }
    if (!member.roles.cache.has(roleId)) return;
    await member.roles.remove(roleId, "Temporary role expired");
    const channel = guild.channels.cache.get(channelId);
    if (!channel?.isTextBased()) return;
    const notice = embed(`Removed <@&${roleId}> from ${member.toString()}. Its time is up.`);
    await channel.send({ embeds: [notice] }).catch(() => undefined);
  },
});

type Grant = Omit<TempRole, "channelId">;

/** Cancels pending expiries of this role for this member. Returns how many there were. */
export function cancelExpiry({ guildId, userId, roleId }: Grant): number {
  return expireTempRole
    .pending()
    .filter(
      ({ payload }) =>
        payload.guildId === guildId && payload.userId === userId && payload.roleId === roleId,
    )
    .filter(({ id }) => expireTempRole.cancel(id)).length;
}

/** Sets when the role expires, replacing an earlier time. */
export function scheduleExpiry(grant: TempRole, runAt: Date): void {
  cancelExpiry(grant);
  expireTempRole.schedule(runAt, grant);
}
