import { describe, expect, it } from "vitest";

import { mapPlays, mapProfile, mapRecent, musicUrl, readLastfmError } from "./lastfm-data.ts";

const image = (url: string, size: string) => ({ "#text": url, size });

const track = (nowPlaying: boolean) => ({
  name: "Song",
  url: "https://www.last.fm/music/Band/_/Song",
  artist: { "#text": "Band", mbid: "" },
  album: { "#text": "Record", mbid: "" },
  image: [image("small.png", "small"), image("large.png", "large"), image("", "extralarge")],
  ...(nowPlaying ? { "@attr": { nowplaying: "true" } } : {}),
});

describe("mapProfile", () => {
  it("reads user.getInfo", () => {
    const profile = mapProfile({
      user: {
        name: "Someone",
        url: "https://www.last.fm/user/Someone",
        playcount: "1234",
        registered: { unixtime: "1600000000", "#text": 1_600_000_000 },
        image: [image("a.png", "small"), image("b.png", "large")],
      },
    });
    expect(profile).toEqual({
      username: "Someone",
      url: "https://www.last.fm/user/Someone",
      scrobbles: 1234,
      registeredAt: new Date(1_600_000_000_000),
      avatarUrl: "b.png",
    });
  });
});

describe("mapRecent", () => {
  it("reads a track list with a playing track", () => {
    const recent = mapRecent({
      recenttracks: { track: [track(true), track(false)], "@attr": { total: "50" } },
    });
    expect(recent).toEqual({
      total: 50,
      track: {
        name: "Song",
        url: "https://www.last.fm/music/Band/_/Song",
        artist: "Band",
        album: "Record",
        imageUrl: "large.png",
        nowPlaying: true,
      },
    });
  });

  it("reads a single track sent as an object", () => {
    const recent = mapRecent({ recenttracks: { track: track(false), "@attr": { total: "1" } } });
    expect(recent.track?.nowPlaying).toBe(false);
  });

  it("reads an empty history and an empty album", () => {
    expect(mapRecent({ recenttracks: { track: [], "@attr": { total: "0" } } }).track).toBe(
      undefined,
    );
    const noAlbum = { ...track(true), album: { "#text": "" } };
    const recent = mapRecent({ recenttracks: { track: [noAlbum], "@attr": { total: "3" } } });
    expect(recent.track?.album).toBeUndefined();
  });
});

describe("mapPlays", () => {
  it("reads play counts and treats missing ones as 0", () => {
    expect(
      mapPlays(
        { track: { userplaycount: "7" } },
        { artist: { stats: { userplaycount: "40" } } },
        undefined,
      ),
    ).toEqual({ track: 7, artist: 40, album: 0 });
  });
});

describe("helpers", () => {
  it("builds music links with plus signs", () => {
    expect(musicUrl("Daft Punk", "Random Access/Memories")).toBe(
      "https://www.last.fm/music/Daft+Punk/Random+Access%2FMemories",
    );
  });

  it("reads Last.fm error bodies", () => {
    expect(readLastfmError({ error: 6, message: "User not found" })?.error).toBe(6);
    expect(readLastfmError({ user: {} })).toBeUndefined();
  });
});
