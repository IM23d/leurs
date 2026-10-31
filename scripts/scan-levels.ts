// Counts every member's messages in one server by reading the channel history, then sets their
// level from that count, with the same rule as /levels set (15 XP per message).
//
// Usage: npm run scan:levels -- <server ID> [--apply]
// Without --apply it only prints what it would change.
//
// Levels are shared across servers, so a count never lowers a member's stored messages.
import { Client, GatewayIntentBits, type GuildTextBasedChannel } from "discord.js";

import { loadConfig } from "#app/config.ts";
import { openDb } from "#db/client.ts";
import { BASE_MESSAGE_XP, levelForXp } from "#modules/levels/levels.math.ts";
import { getStats, setMessages } from "#modules/levels/levels.service.ts";

import { forEachMessage, readableChannels } from "./lib/channel-history.ts";

const [guildId, ...flags] = process.argv.slice(2);
const apply = flags.includes("--apply");
if (!guildId || !/^\d{17,20}$/.test(guildId)) {
  console.error("Usage: npm run scan:levels -- <server ID> [--apply]");
  process.exit(1);
}

/** Adds the author of each message to `counts`. Bots are skipped. */
const countChannel = (channel: GuildTextBasedChannel, counts: Map<string, number>) =>
  forEachMessage(channel, (message) => {
    if (!message.author.bot) {
      counts.set(message.author.id, (counts.get(message.author.id) ?? 0) + 1);
    }
  });

const config = loadConfig();
openDb(config.DATABASE_PATH);
const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMembers,
    GatewayIntentBits.GuildMessages,
  ],
});
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

  // Names are only for the table, so a failed lookup must not throw away the scan.
  const members = await guild.members.fetch().catch(() => guild.members.cache);
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
