import { and, count, eq, max } from "drizzle-orm";

import { db } from "#db/client.ts";

import { roleBackups } from "./roles.schema.ts";

export interface MemberRoles {
  readonly userId: string;
  readonly roleIds: readonly string[];
}

const ofMember = (guildId: string, userId: string) =>
  and(eq(roleBackups.guildId, guildId), eq(roleBackups.userId, userId));

/** Replaces a member's backup. A member without roles has no backup. */
export function saveBackup(
  guildId: string,
  { userId, roleIds }: MemberRoles,
  updatedAt = new Date(),
): void {
  if (roleIds.length === 0) {
    db().delete(roleBackups).where(ofMember(guildId, userId)).run();
    return;
  }
  const values = { roleIds: [...roleIds], updatedAt };
  db()
    .insert(roleBackups)
    .values({ guildId, userId, ...values })
    .onConflictDoUpdate({ target: [roleBackups.guildId, roleBackups.userId], set: values })
    .run();
}

/** Saves many members at once. Returns how many have roles to back up. */
export function saveBackups(
  guildId: string,
  members: readonly MemberRoles[],
  updatedAt = new Date(),
): number {
  db().transaction(() => {
    members.forEach((member) => {
      saveBackup(guildId, member, updatedAt);
    });
  });
  return members.filter(({ roleIds }) => roleIds.length > 0).length;
}

export function getBackup(guildId: string, userId: string): string[] {
  const row = db()
    .select({ roleIds: roleBackups.roleIds })
    .from(roleBackups)
    .where(ofMember(guildId, userId))
    .get();
  return row?.roleIds ?? [];
}

/** Drops one role, so a role that was taken away while the member was gone is not restored. */
export function removeFromBackup(guildId: string, userId: string, roleId: string): void {
  const roleIds = getBackup(guildId, userId);
  if (!roleIds.includes(roleId)) return;
  saveBackup(guildId, { userId, roleIds: roleIds.filter((id) => id !== roleId) });
}

export function backupStatus(guildId: string): { members: number; lastUpdate: Date | undefined } {
  const row = db()
    .select({ members: count(), lastUpdate: max(roleBackups.updatedAt) })
    .from(roleBackups)
    .where(eq(roleBackups.guildId, guildId))
    .get();
  return { members: row?.members ?? 0, lastUpdate: row?.lastUpdate ?? undefined };
}
