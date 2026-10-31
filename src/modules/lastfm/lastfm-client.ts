import { config } from "#app/config.ts";
import { UserError } from "#core/errors.ts";

import {
  mapPlays,
  mapProfile,
  mapRecent,
  NOT_FOUND_CODE,
  readLastfmError,
  type Plays,
  type Profile,
  type Recent,
  type Track,
} from "./lastfm-data.ts";

const API_URL = "https://ws.audioscrobbler.com/2.0/";
const TIMEOUT_MS = 10_000;

class LastfmError extends Error {
  readonly code: number;

  constructor(code: number, message: string) {
    super(`Last.fm error ${code}: ${message}`);
    this.code = code;
  }
}

function apiKey(): string {
  const key = config().LASTFM_API_KEY;
  if (!key) throw new UserError("Last.fm is not configured.");
  return key;
}

/** Throws when Last.fm is not configured, so commands fail before doing any work. */
export const requireLastfm = (): void => void apiKey();

async function call(method: string, params: Record<string, string>): Promise<unknown> {
  const query = new URLSearchParams({ method, ...params, api_key: apiKey(), format: "json" });
  const response = await fetch(`${API_URL}?${query.toString()}`, {
    signal: AbortSignal.timeout(TIMEOUT_MS),
  });
  const body: unknown = await response.json().catch(() => undefined);
  const error = readLastfmError(body);
  if (error) throw new LastfmError(error.error, error.message);
  if (!response.ok) throw new Error(`Last.fm answered with status ${response.status}`);
  return body;
}

const userNotFound = (username: string) => (error: unknown) => {
  if (error instanceof LastfmError && error.code === NOT_FOUND_CODE) {
    throw new UserError(`There is no Last.fm user called \`${username}\`.`);
  }
  throw error;
};

export const fetchProfile = (username: string): Promise<Profile> =>
  call("user.getInfo", { user: username }).then(mapProfile, userNotFound(username));

export const fetchRecent = (username: string): Promise<Recent> =>
  call("user.getRecentTracks", { user: username, limit: "1" }).then(
    mapRecent,
    userNotFound(username),
  );

/** The user's play counts for a track, its artist and its album, fetched in parallel. */
export async function fetchPlays(username: string, track: Track): Promise<Plays> {
  const optional = (method: string, params: Record<string, string>) =>
    call(method, { ...params, username }).catch(() => undefined);
  const [trackInfo, artistInfo, albumInfo] = await Promise.all([
    optional("track.getInfo", { artist: track.artist, track: track.name }),
    optional("artist.getInfo", { artist: track.artist }),
    track.album === undefined
      ? undefined
      : optional("album.getInfo", { artist: track.artist, album: track.album }),
  ]);
  return mapPlays(trackInfo, artistInfo, albumInfo);
}
