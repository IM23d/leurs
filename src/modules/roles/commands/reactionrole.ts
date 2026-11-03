import { PermissionFlagsBits } from "discord.js";

import { defineCommand, subcommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";
import { parseEmoji, type ParsedEmoji } from "#shared/lib/emoji.ts";
import { messageLink, parseMessageRef } from "#shared/lib/message-link.ts";
import { embed, successEmbed } from "#shared/ui/embeds.ts";
import { definePaginator, paginate } from "#shared/ui/paginator.ts";

import {
  addReactionRole,
  listReactionRoles,
  removeReactionRole,
  type ReactionRole,
} from "../reaction-roles.service.ts";
import { fetchMessage, reactionTarget } from "../reaction-target.ts";
import { assertAssignable } from "../role-access.ts";

const PAGE_SIZE = 15;

const emojiFrom = (text: string): ParsedEmoji => {
  const parsed = parseEmoji(text);
  if (!parsed) throw new UserError(`\`${text}\` is not an emoji.`);
  return parsed;
};

const describeLink = ({ guildId, channelId, messageId, emoji, roleId }: ReactionRole) =>
  `${emoji} <@&${roleId}> on ${channelId ? messageLink(guildId, channelId, messageId) : `message \`${messageId}\``}`;

export const reactionRoleList = definePaginator({
  id: "reactionrole-list",
  render: ({ guild, page }) => {
    const all = listReactionRoles(guild.id);
    const { items, page: current, pageCount } = paginate(all, page, PAGE_SIZE);
    const shown =
      all.length === 0
        ? embed("No reaction roles yet. Add one with `/reactionrole add`.")
        : embed(items.map(describeLink).join("\n")).setFooter({
            text: `Page ${current} of ${pageCount}`,
          });
    return { embed: shown.setTitle("Reaction roles"), pageCount };
  },
});

export const reactionroleCommand = defineCommand({
  name: "reactionrole",
  description: "Give roles to members who react to a message",
  permissions: PermissionFlagsBits.ManageRoles,
  subcommands: {
    add: subcommand({
      description: "Give a role for reacting with an emoji",
      aliases: ["reactrole"],
      options: {
        role: opt.role("The role to give"),
        emoji: opt.string("The emoji to react with"),
        message: opt.string("A message link or ID, or text to post as a new message").rest(),
      },
      run: async (ctx, { role, emoji, message }) => {
        assertAssignable(ctx, role);
        const parsed = emojiFrom(emoji);
        const target = await reactionTarget(ctx, message);
        try {
          await target.message.react(parsed.text);
        } catch {
          if (target.created) await target.message.delete().catch(() => undefined);
          throw new UserError(
            `I can't react with ${parsed.text}. Use an emoji from a server I'm in.`,
          );
        }
        addReactionRole({
          guildId: ctx.guild.id,
          channelId: target.message.channelId,
          messageId: target.message.id,
          emojiKey: parsed.key,
          emoji: parsed.text,
          roleId: role.id,
        });
        await ctx.reply({
          embeds: [
            successEmbed(
              `Reacting with ${parsed.text} on ${target.message.url} gives ${role.toString()}.`,
            ),
          ],
          private: true,
        });
      },
    }),
    remove: subcommand({
      description: "Stop giving a role for an emoji",
      options: {
        message: opt.string("The message link or ID"),
        emoji: opt.string("The emoji"),
      },
      run: async (ctx, { message, emoji }) => {
        const ref = parseMessageRef(message);
        if (!ref) throw new UserError("Give a message link or ID.");
        const parsed = emojiFrom(emoji);
        const removed = removeReactionRole(ctx.guild.id, ref.messageId, parsed.key);
        if (!removed) throw new UserError(`${parsed.text} gives no role on that message.`);
        const channelId = removed.channelId ?? ref.channelId;
        const posted = await fetchMessage(ctx, { ...ref, channelId }).catch(() => undefined);
        await posted?.reactions.cache
          .get(parsed.customId ?? parsed.text)
          ?.users.remove(ctx.client.user.id)
          .catch(() => undefined);
        await ctx.reply(successEmbed(`${parsed.text} no longer gives <@&${removed.roleId}>.`));
      },
    }),
    list: subcommand({
      description: "Show every reaction role",
      run: (ctx) => reactionRoleList.reply(ctx),
    }),
  },
});
