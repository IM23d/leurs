import { PermissionFlagsBits, type GuildMember } from "discord.js";

import type { CommandContext } from "#core/commands/context.ts";
import { defineCommand, subcommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";
import { successEmbed } from "#shared/ui/embeds.ts";

import { asBot, assertBotAbove, assertCallerAbove } from "../guards.ts";
import { previousNickname, recordNicknameChange } from "../nicknames.service.ts";
import { mentionedMember } from "../options.ts";

const MAX_NICKNAME_LENGTH = 32;

/** Anyone may change their own nickname. Changing someone else's needs Manage Nicknames. */
function targetOf(ctx: CommandContext, user: GuildMember | undefined): GuildMember {
  const target = user ?? ctx.member;
  if (target.id !== ctx.user.id) {
    if (!ctx.member.permissions.has(PermissionFlagsBits.ManageNicknames)) {
      throw new UserError("You need the Manage Nicknames permission to change someone else's.");
    }
    assertCallerAbove(ctx, target);
  }
  assertBotAbove(target);
  return target;
}

async function changeNickname(
  ctx: CommandContext,
  target: GuildMember,
  nickname: string | null,
): Promise<void> {
  const old = target.nickname;
  await asBot("change nicknames", () => target.setNickname(nickname));
  recordNicknameChange(ctx.guild.id, target.id, old, nickname);
  const whose = target.id === ctx.user.id ? "Your" : `${target.toString()}'s`;
  await ctx.reply(
    successEmbed(
      nickname === null
        ? `${whose} nickname was removed.`
        : `${whose} nickname is now **${nickname}**.`,
    ),
  );
}

// Prefix order is member first, like the old `-nick @user name`. The member is read only from a
// mention or ID, so `-nick New Name` renames the caller instead of looking up "New" as a member.
const userOption = mentionedMember("Whose nickname. Leave empty for yours").optional();

export const nickCommand = defineCommand({
  name: "nick",
  description: "Change, remove or revert a nickname",
  defaultSubcommand: "set",
  subcommands: {
    set: subcommand({
      description: "Set a nickname",
      aliases: ["nickme"],
      options: {
        user: userOption,
        nickname: opt.string("The new nickname").rest().max(MAX_NICKNAME_LENGTH),
      },
      run: (ctx, { user, nickname }) => changeNickname(ctx, targetOf(ctx, user), nickname),
    }),
    reset: subcommand({
      description: "Remove a nickname",
      aliases: ["nickremove", "nickmeremove"],
      options: { user: userOption },
      run: (ctx, { user }) => changeNickname(ctx, targetOf(ctx, user), null),
    }),
    revert: subcommand({
      description: "Go back to the nickname before the last change",
      aliases: ["nickrevert", "nickmerevert"],
      options: { user: userOption },
      run: async (ctx, { user }) => {
        const target = targetOf(ctx, user);
        const previous = previousNickname(ctx.guild.id, target.id);
        if (previous === undefined) {
          throw new UserError(`There is no earlier nickname for ${target.toString()}.`);
        }
        await changeNickname(ctx, target, previous);
      },
    }),
  },
});
