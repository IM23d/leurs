import type { VoiceState } from "discord.js";

import { defineEvent } from "#core/events.ts";

import { setVoiceActive } from "../activity.service.ts";

/** Voice time counts in any voice channel except the server's AFK channel. */
export const countsAsVoiceTime = (state: VoiceState): boolean =>
  state.channelId !== null && state.channelId !== state.guild.afkChannelId;

export const voiceTimeEvent = defineEvent({
  name: "voiceStateUpdate",
  run: (_before, after) => {
    if (!after.member?.user.bot) setVoiceActive(after.id, countsAsVoiceTime(after));
    return Promise.resolve();
  },
});
