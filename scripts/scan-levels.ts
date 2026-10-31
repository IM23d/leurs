// Counts every member's messages in one server by reading the channel history, then sets their
// level from that count, with the same rule as /levels set (15 XP per message).
//
// Usage: npm run scan:levels -- <server ID> [--apply]
// Without --apply it only prints what it would change.
//
// Levels are shared across servers, so a count never lowers a member's stored messages.
import {
  ChannelType,
  Client,
  GatewayIntentBits,
  PermissionFlagsBits,
  type Guild,
  type GuildTextBasedChannel,
} from "discord.js";

import { loadConfig } from "#app/config.ts";
import { openDb } from "#db/client.ts";
import { BASE_MESSAGE_XP, levelForXp } from "#modules/levels/levels.math.ts";
import { getStats, setMessages } from "#modules/levels/levels.service.ts";

const PAGE_SIZE = 100;
const TEXT_CHANNELS = new Set([
  ChannelType.GuildText,
  ChannelType.GuildAnnouncement,
  ChannelType.GuildVoice,
  ChannelType.GuildStageVoice,
  ChannelType.PublicThread,
  ChannelType.PrivateThread,
  ChannelType.AnnouncementThread,
]);

const [guildId, ...flags] = process.argv.slice(2);
const apply = flags.includes("--apply");
if (!guildId || !/^\d{17,20}$/.test(guildId)) {
  console.error("Usage: npm run scan:levels -- <server ID> [--apply]");
  process.exit(1);
}

/** Text channels and active threads the bot can read. */
async function readableChannels(guild: Guild): Promise<GuildTextBasedChannel[]> {
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

/** Adds the authors of every message in the channel to `counts`. Bots are skipped. */
async function countChannel(channel: GuildTextBasedChannel, counts: Map<string, number>) {
  let before: string | undefined;
  let total = 0;
  for (;;) {
    const page = await channel.messages.fetch({ limit: PAGE_SIZE, ...(before ? { before } : {}) });
    for (const message of page.values()) {
      if (!message.author.bot) {
        counts.set(message.author.id, (counts.get(message.author.id) ?? 0) + 1);
      }
    }
    total += page.size;
    before = page.lastKey();
    if (page.size < PAGE_SIZE || !before) return total;
    if (total % 5000 === 0) console.log(`  #${channel.name}: ${total} messages so far`);
  }
}

const config = loadConfig();
openDb(config.DATABASE_PATH);
const client = new Client({ intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages] });
await client.login(config.DISCORD_TOKEN);

try {
  const guild = await client.guilds.fetch(guildId);
  const channels = await readableChannels(guild);
  console.log(`Scanning ${channels.length} channels in ${guild.name}…`);
  const counts = new Map<string, number>();
  for (const channel of channels) {
    const total = await countChannel(channel, counts).catch((error: unknown) => {
      console.warn(`  Skipped #${channel.name}: ${String(error)}`);
      return 0;
    });
    console.log(`  #${channel.name}: ${total} messages`);
  }

  const changes = [...counts]
    .map(([userId, messages]) => ({ userId, messages, before: getStats(userId) }))
    .filter(({ messages, before }) => messages > before.messages)
    .toSorted((a, b) => b.messages - a.messages);

  const members = await guild.members.fetch();
  const name = (userId: string) => members.get(userId)?.user.username ?? `left (${userId})`;
  console.log(`\n${counts.size} people wrote messages. ${changes.length} would go up:`);
  console.table(
    changes.map(({ userId, messages, before }) => ({
      member: name(userId),
      "messages before": before.messages,
      "level before": before.level,
      "messages counted": messages,
      "level after": levelForXp(messages * BASE_MESSAGE_XP),
    })),
  );

  if (apply) {
    for (const { userId, messages } of changes) setMessages(userId, messages);
    console.log(`Updated ${changes.length} members.`);
  } else {
    console.log("Nothing was changed. Run again with --apply to save these levels.");
  }
} finally {
  await client.destroy();
}
