import { levelForXp, rollMessageXp } from "./levels.math.ts";
import { addPending, flushLevels, getStats } from "./levels.service.ts";

const RATE_WINDOW_MS = 60_000;
const MAX_MESSAGES_PER_WINDOW = 60;

/** Per user: when the current rate window started and how many messages it has seen. */
const rateWindows = new Map<string, { start: number; count: number }>();

/** Per user: when the uncredited part of their current voice session started. */
const voiceSessions = new Map<string, number>();

/** Like the old bot, a user earns XP for at most 60 messages per 60 second window. */
function withinRateLimit(userId: string, now: number): boolean {
  const window = rateWindows.get(userId);
  const current =
    window && now - window.start <= RATE_WINDOW_MS
      ? { ...window, count: window.count + 1 }
      : { start: now, count: 1 };
  rateWindows.set(userId, current);
  return current.count <= MAX_MESSAGES_PER_WINDOW;
}

/**
 * Counts a chat message towards XP. Returns the new level when the message crossed into one,
 * so the caller can announce it.
 */
export function recordMessage(
  userId: string,
  now = Date.now(),
  random: () => number = Math.random,
): number | undefined {
  if (!withinRateLimit(userId, now)) return undefined;
  const before = getStats(userId);
  const xp = rollMessageXp(random);
  addPending(userId, { xp, messages: 1 });
  const level = levelForXp(before.xp + xp);
  return level > before.level ? level : undefined;
}

/** Credits the whole seconds of a session since its start and moves the start forward. */
function creditVoice(userId: string, start: number, now: number): void {
  const seconds = Math.floor((now - start) / 1000);
  if (seconds > 0) addPending(userId, { voiceSeconds: seconds });
  voiceSessions.set(userId, start + seconds * 1000);
}

/**
 * Starts or ends voice time tracking. `active` means the user is in a voice channel that is not
 * the server's AFK channel. Moving between active channels keeps the session running.
 */
export function setVoiceActive(userId: string, active: boolean, now = Date.now()): void {
  const start = voiceSessions.get(userId);
  if (active && start === undefined) voiceSessions.set(userId, now);
  if (!active && start !== undefined) {
    creditVoice(userId, start, now);
    voiceSessions.delete(userId);
  }
}

/**
 * Matches the running sessions to the users now in a counted voice channel: ends the sessions
 * of everyone else and starts sessions for anyone new. Voice events can go missing, for example
 * when the bot leaves a server or reconnects, so this runs before every flush.
 */
export function syncVoiceSessions(activeUserIds: ReadonlySet<string>, now = Date.now()): void {
  [...voiceSessions.keys()]
    .filter((userId) => !activeUserIds.has(userId))
    .forEach((userId) => {
      setVoiceActive(userId, false, now);
    });
  activeUserIds.forEach((userId) => {
    setVoiceActive(userId, true, now);
  });
}

/** Credits running voice sessions, then writes every pending gain to the database. */
export function flushActivity(now = Date.now()): number {
  for (const [userId, start] of voiceSessions) creditVoice(userId, start, now);
  return flushLevels();
}
