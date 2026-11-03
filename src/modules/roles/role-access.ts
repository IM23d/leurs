import { PermissionFlagsBits, type GuildMember, type Role } from "discord.js";

import type { CommandContext } from "#core/commands/context.ts";
import { UserError } from "#core/errors.ts";

/** Refuses roles the bot cannot give, or that sit at or above the caller's highest role. */
export function assertAssignable(ctx: CommandContext, role: Role): void {
  const me = ctx.guild.members.me;
  if (role.id === ctx.guild.id) throw new UserError("Pick a role other than @everyone.");
  if (role.managed) {
    throw new UserError(
      `${role.toString()} is managed by an integration, so nobody can assign it.`,
    );
  }
  if (!me?.permissions.has(PermissionFlagsBits.ManageRoles)) {
    throw new UserError("I need the Manage Roles permission.");
  }
  if (me.roles.highest.comparePositionTo(role) <= 0) {
    throw new UserError(`${role.toString()} is at or above my highest role.`);
  }
  const isOwner = ctx.guild.ownerId === ctx.user.id;
  if (!isOwner && ctx.member.roles.highest.comparePositionTo(role) <= 0) {
    throw new UserError(`${role.toString()} is at or above your highest role.`);
  }
}

/** The roles worth backing up: all but @everyone and roles that an integration manages. */
export const backupRoleIds = (member: GuildMember): string[] =>
  member.roles.cache
    .filter((role) => role.id !== member.guild.id && !role.managed)
    .map((role) => role.id);
