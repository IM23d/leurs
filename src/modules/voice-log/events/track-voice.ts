import type { Guild } from "discord.js";

import { defineEvent } from "#core/events.ts";
import { getSettings } from "#modules/settings/api.ts";
import { logger } from "#shared/lib/logger.ts";

import { join, leave, type VoiceStay } from "../voice-log.service.ts";
import { leftEmbed } from "../voice-log.views.ts";

async function postLeave(guild: Guild, stay: VoiceStay & { leftAt: Date }): Promise<void> {
  const channelId = getSettings(guild.id).voiceLogChannelId;
  if (channelId === null) return;
  const channel = guild.channels.cache.get(channelId);
  if (!channel?.isSendable()) return;
  await channel.send({ embeds: [leftEmbed(stay, new Date())] }).catch((error: unknown) => {
    logger.warn({ err: error, guild: guild.id }, "Could not post to the voice log channel");
  });
}

/** Records joins, leaves and moves. Mute, deafen and stream changes are ignored. */
export const trackVoiceEvent = defineEvent({
  name: "voiceStateUpdate",
  run: async (before, after) => {
    if (before.channelId === after.channelId || after.member?.user.bot) return;
    const now = new Date();
    const { guild, id: userId } = after;
    if (before.channelId !== null) {
      const stay = leave(guild.id, userId, now);
      if (stay?.leftAt) await postLeave(guild, { ...stay, leftAt: stay.leftAt });
    }
    if (after.channelId !== null) {
      join({ guildId: guild.id, channelId: after.channelId, userId }, now);
    }
  },
});
