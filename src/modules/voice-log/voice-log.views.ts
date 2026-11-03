import { time, TimestampStyles, type EmbedBuilder } from "discord.js";

import { formatShortDuration } from "#shared/lib/duration.ts";
import { joinWithin } from "#shared/lib/text.ts";
import { embed } from "#shared/ui/embeds.ts";

import type { VoiceStay } from "./voice-log.service.ts";

const SAME_DAY_MS = 12 * 3_600_000;

const joined = (stay: VoiceStay) => time(stay.joinedAt, TimestampStyles.LongDateShortTime);

/** Leave time, with the date only when the stay was long enough to cross into another day. */
const left = (stay: VoiceStay, leftAt: Date) =>
  time(
    leftAt,
    leftAt.getTime() - stay.joinedAt.getTime() < SAME_DAY_MS
      ? TimestampStyles.ShortTime
      : TimestampStyles.LongDateShortTime,
  );

const stayed = (stay: VoiceStay, now: Date) =>
  formatShortDuration((stay.leftAt ?? now).getTime() - stay.joinedAt.getTime());

/** "Joined 18:02 · left 18:45 · 43m", or "still here" for an open stay. */
const stayTimes = (stay: VoiceStay, now: Date): string =>
  stay.leftAt
    ? `Joined ${joined(stay)} · left ${left(stay, stay.leftAt)} · ${stayed(stay, now)}`
    : `Joined ${joined(stay)} · still here · ${stayed(stay, now)}`;

export const historyLine = (stay: VoiceStay, now: Date): string =>
  `<@${stay.userId}> in <#${stay.channelId}>\n${stayTimes(stay, now)}`;

/** Who is in which call right now, grouped by channel. */
export function liveEmbed(stays: readonly VoiceStay[], now: Date): EmbedBuilder {
  const byChannel = Map.groupBy(stays, (stay) => stay.channelId);
  const sections = [...byChannel].map(([channelId, members]) =>
    [
      `**<#${channelId}>** · ${members.length} ${members.length === 1 ? "person" : "people"}`,
      ...members.map(
        (stay) =>
          `<@${stay.userId}> since ${time(stay.joinedAt, TimestampStyles.ShortTime)} · ${stayed(stay, now)}`,
      ),
    ].join("\n"),
  );
  const text = joinWithin(sections, {
    separator: "\n\n",
    more: (hidden) => `And ${hidden} more channels.`,
  });
  return embed(text || "Nobody is in a voice channel right now.").setTitle("In voice now");
}

/** Posted to the voice log channel when someone leaves a call. */
export const leftEmbed = (stay: VoiceStay & { leftAt: Date }, now: Date): EmbedBuilder =>
  embed(`<@${stay.userId}> left <#${stay.channelId}>\n${stayTimes(stay, now)}`);
