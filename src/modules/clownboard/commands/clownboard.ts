import { ChannelType, PermissionFlagsBits } from "discord.js";

import { defineCommand, subcommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";
import { formatDuration } from "#shared/lib/duration.ts";
import { parseEmoji } from "#shared/lib/emoji.ts";
import { parseMessageRef } from "#shared/lib/message-link.ts";
import { successEmbed } from "#shared/ui/embeds.ts";

import {
  DEFAULTS,
  disableClownboard,
  enableClownboard,
  findPost,
  getClownboard,
  removePost,
  topClowns,
  updateClownboard,
} from "../clownboard.service.ts";
import { settingsEmbed, topEmbed } from "../clownboard.views.ts";

const ADMIN = PermissionFlagsBits.Administrator;
const TOP_SIZE = 10;

/** Applies a settings change, or explains that the clownboard is off. */
function change(guildId: string, changes: Parameters<typeof updateClownboard>[1]) {
  const updated = updateClownboard(guildId, changes);
  if (!updated) throw new UserError("Turn the clownboard on first with `/clownboard channel`.");
  return updated;
}

export const clownboardCommand = defineCommand({
  name: "clownboard",
  description: "Repost the worst messages: react with the clown emoji",
  aliases: ["cb"],
  defaultSubcommand: "view",
  subcommands: {
    view: subcommand({
      description: "Show the clownboard settings",
      run: async (ctx) => {
        await ctx.reply(settingsEmbed(getClownboard(ctx.guild.id)));
      },
    }),
    top: subcommand({
      description: "Show who got clowned the most",
      run: async (ctx) => {
        const emoji = getClownboard(ctx.guild.id)?.emoji ?? DEFAULTS.emoji;
        await ctx.reply(topEmbed(topClowns(ctx.guild.id, TOP_SIZE), emoji));
      },
    }),
    channel: subcommand({
      description: "Turn the clownboard on and choose its channel",
      permissions: ADMIN,
      options: { channel: opt.channel("Where clowned messages are posted") },
      run: async (ctx, { channel }) => {
        if (channel.type !== ChannelType.GuildText) throw new UserError("Pick a text channel.");
        enableClownboard(ctx.guild.id, channel.id);
        await ctx.reply(successEmbed(`Clowned messages now go to <#${channel.id}>.`));
      },
    }),
    emoji: subcommand({
      description: "Change the emoji that clowns a message",
      permissions: ADMIN,
      options: { emoji: opt.custom("An emoji, e.g. 🤡", "emoji", parseEmoji) },
      run: async (ctx, { emoji }) => {
        change(ctx.guild.id, { emoji: emoji.text, emojiKey: emoji.key });
        await ctx.reply(successEmbed(`React with ${emoji.text} to clown a message.`));
      },
    }),
    threshold: subcommand({
      description: "How many clowns a message needs",
      permissions: ADMIN,
      options: { count: opt.integer("Reactions needed").min(1).max(50) },
      run: async (ctx, { count }) => {
        change(ctx.guild.id, { threshold: count });
        await ctx.reply(successEmbed(`A message needs ${count} to get on the clownboard.`));
      },
    }),
    cooldown: subcommand({
      description: "How long members wait between clowns. Admins never wait",
      permissions: ADMIN,
      options: {
        duration: opt.duration("e.g. 6h. Leave empty or write none for no cooldown").optional(),
      },
      run: async (ctx, { duration }) => {
        change(ctx.guild.id, { cooldownSeconds: Math.round((duration ?? 0) / 1000) });
        await ctx.reply(
          successEmbed(
            duration
              ? `Members can clown once every ${formatDuration(duration)}.`
              : "Members can clown without waiting.",
          ),
        );
      },
    }),
    remove: subcommand({
      description: "Take a message off the clownboard",
      permissions: ADMIN,
      options: {
        message: opt
          .custom(
            "A link or ID of the message or its clownboard post. Or reply to it",
            "message link",
            parseMessageRef,
          )
          .optional(),
      },
      run: async (ctx, { message }) => {
        const messageId = message?.messageId ?? (await ctx.referencedMessage())?.id;
        const post = messageId === undefined ? undefined : findPost(ctx.guild.id, messageId);
        if (!post) throw new UserError("That message is not on the clownboard.");
        removePost(post.messageId);
        const board = getClownboard(ctx.guild.id);
        const channel = board ? ctx.guild.channels.cache.get(board.channelId) : undefined;
        if (channel?.isTextBased()) {
          await channel.messages.delete(post.boardMessageId).catch(() => undefined);
        }
        await ctx.reply(successEmbed("Taken off the clownboard."));
      },
    }),
    off: subcommand({
      description: "Turn the clownboard off. Past posts stay",
      permissions: ADMIN,
      run: async (ctx) => {
        if (!disableClownboard(ctx.guild.id)) throw new UserError("The clownboard is already off.");
        await ctx.reply(successEmbed("The clownboard is off."));
      },
    }),
  },
});
