import type { EmbedBuilder, Guild } from "discord.js";

import { getSettings } from "#modules/settings/api.ts";
import { logger } from "#shared/lib/logger.ts";

import { logEntryEmbed, type LogEntry } from "./moderation.views.ts";

type LogChannel = "modLogChannelId" | "blockedTermsLogChannelId";

/** Posts to a log channel from the server settings. Does nothing when the channel is not set. */
export async function postLog(guild: Guild, channel: LogChannel, entry: EmbedBuilder) {
  const id = getSettings(guild.id)[channel];
  if (id === null) return;
  const target = guild.channels.cache.get(id);
  if (!target?.isTextBased()) return;
  await target.send({ embeds: [entry] }).catch((error: unknown) => {
    logger.warn(
      { err: error, guildId: guild.id, channelId: id },
      "Could not post to a log channel",
    );
  });
}

export const logModAction = (guild: Guild, entry: LogEntry): Promise<void> =>
  postLog(guild, "modLogChannelId", logEntryEmbed(entry));
