import { z } from "zod";

// Mapping of Last.fm API responses. Kept free of HTTP so it is testable with sample JSON.

export interface Profile {
  readonly username: string;
  readonly url: string;
  readonly scrobbles: number;
  readonly registeredAt: Date;
  readonly avatarUrl: string | undefined;
}

export interface Track {
  readonly name: string;
  readonly url: string;
  readonly artist: string;
  readonly album: string | undefined;
  readonly imageUrl: string | undefined;
  readonly nowPlaying: boolean;
}

export interface Recent {
  /** The newest track, or undefined when the user never scrobbled. */
  readonly track: Track | undefined;
  readonly total: number;
}

export interface Plays {
  readonly track: number;
  readonly artist: number;
  readonly album: number;
}

const text = z.object({ "#text": z.string() });
const images = z.array(text).optional();

const nonEmpty = (value: string | undefined) => (value === "" ? undefined : value);

/** Last.fm lists images smallest first, with empty URLs for missing sizes. */
const largestImage = (list: z.infer<typeof images>) =>
  list?.map((image) => image["#text"]).findLast((url) => url !== "");

const userInfo = z.object({
  user: z.object({
    name: z.string(),
    url: z.string(),
    playcount: z.coerce.number(),
    registered: z.object({ unixtime: z.coerce.number() }),
    image: images,
  }),
});

const track = z.object({
  name: z.string(),
  url: z.string(),
  artist: text,
  album: text.optional(),
  image: images,
  "@attr": z.object({ nowplaying: z.string() }).optional(),
});

const recentTracks = z.object({
  recenttracks: z.object({
    // A single track comes back as an object instead of a list.
    track: z.union([z.array(track), track]).optional(),
    "@attr": z.object({ total: z.coerce.number() }),
  }),
});

const playcount = z.coerce.number().catch(0);
const trackInfo = z.object({ track: z.object({ userplaycount: playcount }) });
const artistInfo = z.object({
  artist: z.object({ stats: z.object({ userplaycount: playcount }) }),
});
const albumInfo = z.object({ album: z.object({ userplaycount: playcount }) });

const lastfmError = z.object({ error: z.number(), message: z.string() });

/** Last.fm's error body, which it sends with status 200 for some errors. */
export const readLastfmError = (json: unknown) => lastfmError.safeParse(json).data;

/** Error code Last.fm uses for a user, track or album that does not exist. */
export const NOT_FOUND_CODE = 6;

export function mapProfile(json: unknown): Profile {
  const { user } = userInfo.parse(json);
  return {
    username: user.name,
    url: user.url,
    scrobbles: user.playcount,
    registeredAt: new Date(user.registered.unixtime * 1000),
    avatarUrl: largestImage(user.image),
  };
}

export function mapRecent(json: unknown): Recent {
  const { recenttracks } = recentTracks.parse(json);
  const tracks = [recenttracks.track ?? []].flat();
  const newest = tracks[0];
  return {
    total: recenttracks["@attr"].total,
    track: newest && {
      name: newest.name,
      url: newest.url,
      artist: newest.artist["#text"],
      album: nonEmpty(newest.album?.["#text"]),
      imageUrl: largestImage(newest.image),
      nowPlaying: newest["@attr"]?.nowplaying === "true",
    },
  };
}

/** Plays read as 0 when Last.fm does not know the track, artist or album. */
export const mapPlays = (track: unknown, artist: unknown, album: unknown): Plays => ({
  track: trackInfo.safeParse(track).data?.track.userplaycount ?? 0,
  artist: artistInfo.safeParse(artist).data?.artist.stats.userplaycount ?? 0,
  album: albumInfo.safeParse(album).data?.album.userplaycount ?? 0,
});

/** A last.fm/music link. Last.fm writes spaces as "+". */
export const musicUrl = (...parts: readonly string[]): string =>
  `https://www.last.fm/music/${parts.map((part) => encodeURIComponent(part).replaceAll("%20", "+")).join("/")}`;
