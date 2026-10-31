// Imports past Wordle results from the Wordle app's daily summaries.
//
// Usage: npm run scan:wordle -- <server ID> [channel ID]
// With a channel ID it reads only that channel, which is much faster. Results already stored are
// kept, so it is safe to run again.
import { Client, GatewayIntentBits } from "discord.js";

import { loadConfig } from "#app/config.ts";
import { openDb } from "#db/client.ts";
import { parseDailySummary } from "#modules/wordle/wordle-parse.ts";
import { saveSummary } from "#modules/wordle/wordle.service.ts";

import { forEachMessage, readableChannels } from "./lib/channel-history.ts";

const [guildId, channelId] = process.argv.slice(2);
const isId = (value: string | undefined) => value !== undefined && /^\d{17,20}$/.test(value);
if (!isId(guildId) || (channelId !== undefined && !isId(channelId))) {
  console.error("Usage: npm run scan:wordle -- <server ID> [channel ID]");
  process.exit(1);
}

const config = loadConfig();
openDb(config.DATABASE_PATH);
const client = new Client({
  intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages],
});
await client.login(config.DISCORD_TOKEN);

try {
  const guild = await client.guilds.fetch(guildId ?? "");
  const channels = (await readableChannels(guild)).filter(
    (channel) => channelId === undefined || channel.id === channelId,
  );
  if (channels.length === 0) throw new Error("The bot cannot read that channel.");
  let summaries = 0;
  let saved = 0;
  for (const channel of channels) {
    await forEachMessage(channel, (message) => {
      const summary = message.author.bot
        ? parseDailySummary(message.content, message.createdAt)
        : undefined;
      if (!summary) return;
      summaries += 1;
      saved += saveSummary(guild.id, summary);
    }).catch((error: unknown) => {
      console.warn(`  Skipped #${channel.name}: ${String(error)}`);
    });
  }
  console.log(`Found ${summaries} daily summaries. Saved ${saved} new results.`);
} finally {
  await client.destroy();
}
