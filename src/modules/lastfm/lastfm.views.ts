import { time, TimestampStyles, type EmbedBuilder, type User } from "discord.js";

import { embed } from "#shared/ui/embeds.ts";

import { musicUrl, type Plays, type Profile, type Recent, type Track } from "./lastfm-data.ts";

export interface Listener {
  readonly username: string;
  readonly track: Track;
}

const profileUrl = (username: string) => `https://www.last.fm/user/${encodeURIComponent(username)}`;

const author = (username: string, user: User) => ({
  name: `Last.fm: ${username}`,
  iconURL: user.displayAvatarURL(),
  url: profileUrl(username),
});

const trackLine = (track: Track) =>
  `[${track.name}](${track.url}) by [${track.artist}](${musicUrl(track.artist)})`;

export function profileEmbed(profile: Profile, recent: Recent, user: User): EmbedBuilder {
  const lines = [
    `**Scrobbles:** ${profile.scrobbles.toLocaleString("en-US")}`,
    `**Account created:** ${time(profile.registeredAt, TimestampStyles.LongDate)}`,
    ...(recent.track
      ? [
          `**${recent.track.nowPlaying ? "Now playing" : "Last played"}:** ${trackLine(recent.track)}`,
        ]
      : []),
  ];
  const built = embed(lines.join("\n")).setAuthor(author(profile.username, user));
  return profile.avatarUrl ? built.setThumbnail(profile.avatarUrl) : built;
}

export const notPlayingEmbed = (username: string, user: User): EmbedBuilder =>
  embed("Nothing is playing right now.").setAuthor(author(username, user));

export function nowPlayingEmbed(
  username: string,
  user: User,
  recent: Recent & { track: Track },
  plays: Plays,
): EmbedBuilder {
  const { track } = recent;
  const lines = [
    `**Track**\n[${track.name}](${track.url})`,
    `**Artist**\n[${track.artist}](${musicUrl(track.artist)})`,
    ...(track.album ? [`**Album**\n[${track.album}](${musicUrl(track.artist, track.album)})`] : []),
  ];
  const counts = [
    `${plays.artist} artist scrobbles`,
    ...(track.album ? [`${plays.album} album scrobbles`] : []),
    `${plays.track} track scrobbles`,
    `${recent.total} total scrobbles`,
  ];
  const built = embed(lines.join("\n"))
    .setAuthor(author(username, user))
    .setFooter({ text: counts.join(" • ") });
  return track.imageUrl ? built.setThumbnail(track.imageUrl) : built;
}

const MAX_LISTED = 15;

export function serverEmbed(listeners: readonly Listener[], linked: number): EmbedBuilder {
  const hidden = listeners.length - MAX_LISTED;
  const summary =
    listeners.length === 0
      ? `Nobody is listening right now. Members with Last.fm: ${linked}`
      : `Listening: ${listeners.length} of ${linked} members with Last.fm`;
  const lines = listeners
    .slice(0, MAX_LISTED)
    .map(({ username, track }) => `[${username}](${profileUrl(username)})\n${trackLine(track)}`);
  const more = hidden > 0 ? [`And ${hidden} more.`] : [];
  return embed([...lines, ...more, summary].join("\n\n")).setTitle("Playing in this server");
}
