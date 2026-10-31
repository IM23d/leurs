import type { Guild, Role } from "discord.js";

import { UserError } from "#core/errors.ts";
import { getSettings } from "#modules/settings/api.ts";

/** The jail role from the server settings, checked so the bot can hand it out. */
export function jailRole(guild: Guild, prefix: string): Role {
  const id = getSettings(guild.id).jailRoleId;
  const role = id === null ? undefined : guild.roles.cache.get(id);
  if (!role) {
    throw new UserError(
      `No jail role is set. An admin can set one with \`${prefix}settings role jail\`.`,
    );
  }
  if (!role.editable) {
    throw new UserError(`My highest role must be above ${role.toString()} to hand it out.`);
  }
  return role;
}
