import { ChannelType, PermissionFlagsBits } from "discord.js";

import { defineCommand, subcommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";

import { ANY, historyPages } from "../history-pages.ts";
import { openStays } from "../voice-log.service.ts";
import { liveEmbed } from "../voice-log.views.ts";

const voiceChannel = opt.channel("A voice channel").optional();

const assertVoice = (channel: { type: ChannelType } | undefined) => {
  if (
    channel &&
    channel.type !== ChannelType.GuildVoice &&
    channel.type !== ChannelType.GuildStageVoice
  ) {
    throw new UserError("Pick a voice channel.");
  }
};

export const voicelogCommand = defineCommand({
  name: "voicelog",
  description: "See who is in voice now and who was in which call",
  aliases: ["vc", "calls"],
  defaultSubcommand: "now",
  subcommands: {
    now: subcommand({
      description: "Show who is in voice right now and since when",
      options: { channel: voiceChannel },
      run: async (ctx, { channel }) => {
        assertVoice(channel);
        await ctx.reply(liveEmbed(openStays(ctx.guild.id, channel?.id), new Date()));
      },
    }),
    history: subcommand({
      description: "Show past calls with join time, leave time and duration",
      permissions: PermissionFlagsBits.ModerateMembers,
      options: {
        channel: voiceChannel,
        user: opt.user("Only this member").optional(),
        page: opt.integer("Page number").min(1).optional(),
      },
      run: async (ctx, { channel, user, page }) => {
        assertVoice(channel);
        await historyPages.reply(ctx, {
          page: page ?? 1,
          args: [channel?.id ?? ANY, user?.id ?? ANY],
        });
      },
    }),
  },
});
