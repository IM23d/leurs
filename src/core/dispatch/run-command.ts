import { PermissionFlagsBits, PermissionsBitField } from "discord.js";

import { formatDuration } from "#shared/lib/duration.ts";

import type { CommandContext } from "../commands/context.ts";
import { clearCooldown, takeCooldown } from "../cooldowns/cooldowns.ts";
import { UserError } from "../errors.ts";
import type { Route } from "../registry.ts";

const GLOBAL_COOLDOWN_SECONDS = 3;

export interface RunOptions {
  readonly ownerIds: readonly string[];
}

function checkAccess(ctx: CommandContext, route: Route, { ownerIds }: RunOptions): void {
  const { command, leaf } = route;
  if ((command.ownerOnly || leaf.ownerOnly) && !ownerIds.includes(ctx.user.id)) {
    throw new UserError("Only the bot owner can use this command.");
  }
  const needed = [command.permissions, leaf.permissions].filter((p) => p !== undefined);
  const missing = needed.filter((permission) => !ctx.member.permissions.has(permission));
  if (missing.length > 0) {
    const names = new PermissionsBitField(missing.reduce((all, p) => all | p, 0n)).toArray();
    throw new UserError(`You need the ${names.join(", ")} permission to use this command.`);
  }
}

function checkCooldowns(ctx: CommandContext, route: Route): void {
  const isAdmin = ctx.member.permissions.has(PermissionFlagsBits.Administrator);
  if (!isAdmin && takeCooldown("global", ctx.user.id, GLOBAL_COOLDOWN_SECONDS) > 0) {
    throw new UserError(`Slow down a little. Try again in a few seconds.`);
  }
  const seconds = route.leaf.cooldown;
  if (seconds === undefined) return;
  const left = takeCooldown(route.path, ctx.user.id, seconds);
  if (left > 0) {
    throw new UserError(
      `You can use \`${ctx.prefix}${route.path}\` again in ${formatDuration(left)}.`,
    );
  }
}

/**
 * Checks access and cooldowns, then runs the handler. A UserError from the handler refunds the
 * command's cooldown, so a rejected attempt does not count.
 */
export async function runCommand(
  ctx: CommandContext,
  route: Route,
  readValues: () => Promise<Record<string, unknown>>,
  options: RunOptions,
): Promise<void> {
  checkAccess(ctx, route, options);
  const values = await readValues();
  checkCooldowns(ctx, route);
  try {
    await route.leaf.run(ctx, values);
  } catch (error) {
    if (error instanceof UserError && route.leaf.cooldown !== undefined) {
      clearCooldown(route.path, ctx.user.id);
    }
    throw error;
  }
}
