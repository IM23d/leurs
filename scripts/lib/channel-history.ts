import {
  ChannelType,
  PermissionFlagsBits,
  type Guild,
  type GuildTextBasedChannel,
  type Message,
} from "discord.js";

const PAGE_SIZE = 100;
const PROGRESS_EVERY = 5000;
const TEXT_CHANNELS = new Set([
  ChannelType.GuildText,
  ChannelType.GuildAnnouncement,
  ChannelType.GuildVoice,
  ChannelType.GuildStageVoice,
  ChannelType.PublicThread,
  ChannelType.PrivateThread,
  ChannelType.AnnouncementThread,
]);

/** Text channels and active threads the bot can read. */
export async function readableChannels(guild: Guild): Promise<GuildTextBasedChannel[]> {
  const me = await guild.members.fetchMe();
  const channels = [...(await guild.channels.fetch()).values()];
  const threads = [...(await guild.channels.fetchActiveThreads()).threads.values()];
  return [...channels, ...threads].filter(
    (channel): channel is GuildTextBasedChannel =>
      channel !== null &&
      TEXT_CHANNELS.has(channel.type) &&
      channel.isTextBased() &&
      channel
        .permissionsFor(me)
        .has([PermissionFlagsBits.ViewChannel, PermissionFlagsBits.ReadMessageHistory]),
  );
}

/**
 * Calls `onMessage` for every message in the channel, newest first, and returns how many there
 * were. Discord returns 100 messages per request, so long channels take a while.
 */
export async function forEachMessage(
  channel: GuildTextBasedChannel,
  onMessage: (message: Message) => void,
): Promise<number> {
  let before: string | undefined;
  let total = 0;
  for (;;) {
    const page = await channel.messages.fetch({ limit: PAGE_SIZE, ...(before ? { before } : {}) });
    page.forEach(onMessage);
    total += page.size;
    before = page.lastKey();
    if (page.size < PAGE_SIZE || !before) return total;
    if (total % PROGRESS_EVERY === 0) console.log(`  #${channel.name}: ${total} messages so far`);
  }
}
