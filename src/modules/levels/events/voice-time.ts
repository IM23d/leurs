import type { Client, VoiceState } from "discord.js";

import { defineEvent } from "#core/events.ts";

import { setVoiceActive } from "../activity.service.ts";

/** Voice time counts in any voice channel except the server's AFK channel. */
const countsAsVoiceTime = (state: VoiceState): boolean =>
  state.channelId !== null && state.channelId !== state.guild.afkChannelId;

/** Users other than bots who are in a counted voice channel in any server the bot is in. */
export const voiceUserIds = (client: Client): Set<string> =>
  new Set(
    client.guilds.cache
      .flatMap((guild) => guild.voiceStates.cache)
      .filter((state) => !state.member?.user.bot && countsAsVoiceTime(state))
      .map((state) => state.id),
  );

// Voice time is counted per user, not per server. Checking every server keeps a session running
// when someone moves to another server and the join there arrives before the leave here.
const inCountedVoice = (client: Client, userId: string): boolean =>
  client.guilds.cache.some((guild) => {
    const state = guild.voiceStates.cache.get(userId);
    return state !== undefined && countsAsVoiceTime(state);
  });

export const voiceTimeEvent = defineEvent({
  name: "voiceStateUpdate",
  run: (_before, after) => {
    if (!after.member?.user.bot) setVoiceActive(after.id, inCountedVoice(after.client, after.id));
    return Promise.resolve();
  },
});
