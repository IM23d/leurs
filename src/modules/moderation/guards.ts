import { DiscordAPIError, RESTJSONErrorCodes, type GuildMember } from "discord.js";

import type { CommandContext } from "#core/commands/context.ts";
import { UserError } from "#core/errors.ts";

/** Checks that the bot's highest role is above the member's, so Discord lets it act. */
export function assertBotAbove(target: GuildMember): void {
  const { guild } = target;
  const me = guild.members.me;
  if (target.id === guild.ownerId) throw new UserError("I can't act on the server owner.");
  if (!me || target.roles.highest.comparePositionTo(me.roles.highest) >= 0) {
    throw new UserError(`My highest role must be above ${target.toString()}'s.`);
  }
}

/** The server owner outranks everyone, whatever their roles. */
export function assertCallerAbove(ctx: CommandContext, target: GuildMember): void {
  const isOwner = ctx.user.id === ctx.guild.ownerId;
  if (!isOwner && target.roles.highest.comparePositionTo(ctx.member.roles.highest) >= 0) {
    throw new UserError(`${target.toString()} has a role equal to or above yours.`);
  }
}

/** Checks that both the caller and the bot rank above the member. */
export function assertCanModerate(ctx: CommandContext, target: GuildMember): void {
  if (target.id === ctx.user.id) throw new UserError("You can't use this on yourself.");
  assertBotAbove(target);
  assertCallerAbove(ctx, target);
}

/** Runs a Discord call and turns a missing permission into a message for the user. */
export async function asBot<T>(what: string, call: () => Promise<T>): Promise<T> {
  try {
    return await call();
  } catch (error) {
    if (error instanceof DiscordAPIError && error.code === RESTJSONErrorCodes.MissingPermissions) {
      throw new UserError(`I don't have permission to ${what}.`);
    }
    throw error;
  }
}
