import { and, count, desc, eq, isNull, lt, type SQL } from "drizzle-orm";

import { db } from "#db/client.ts";

import { voiceStays, type VoiceStay } from "./voice-log.schema.ts";

export type { VoiceStay } from "./voice-log.schema.ts";

/** Stays older than this are deleted. */
export const RETENTION_MS = 30 * 86_400_000;

export interface Presence {
  readonly guildId: string;
  readonly channelId: string;
  readonly userId: string;
}

const openStayOf = (guildId: string, userId: string) =>
  and(eq(voiceStays.guildId, guildId), eq(voiceStays.userId, userId), isNull(voiceStays.leftAt));

/** Ends the member's open stay in this server and returns it, if there was one. */
export function leave(guildId: string, userId: string, now: Date): VoiceStay | undefined {
  return db()
    .update(voiceStays)
    .set({ leftAt: now, lastSeenAt: now })
    .where(openStayOf(guildId, userId))
    .returning()
    .all()
    .at(0);
}

/** Starts a stay. Ends an open one in the same server first, so a member has at most one. */
export function join({ guildId, channelId, userId }: Presence, now: Date): void {
  leave(guildId, userId, now);
  db()
    .insert(voiceStays)
    .values({ guildId, channelId, userId, joinedAt: now, lastSeenAt: now })
    .run();
}

export function openStays(guildId: string, channelId?: string): VoiceStay[] {
  const filters: SQL[] = [eq(voiceStays.guildId, guildId), isNull(voiceStays.leftAt)];
  if (channelId !== undefined) filters.push(eq(voiceStays.channelId, channelId));
  return db()
    .select()
    .from(voiceStays)
    .where(and(...filters))
    .orderBy(voiceStays.channelId, voiceStays.joinedAt)
    .all();
}

export interface HistoryQuery {
  readonly guildId: string;
  readonly channelId?: string | undefined;
  readonly userId?: string | undefined;
}

const historyFilter = ({ guildId, channelId, userId }: HistoryQuery) =>
  and(
    eq(voiceStays.guildId, guildId),
    channelId === undefined ? undefined : eq(voiceStays.channelId, channelId),
    userId === undefined ? undefined : eq(voiceStays.userId, userId),
  );

/** One page of stays, newest first, and the total number of matching stays. */
export function history(
  query: HistoryQuery,
  offset: number,
  limit: number,
): { stays: VoiceStay[]; total: number } {
  const where = historyFilter(query);
  const stays = db()
    .select()
    .from(voiceStays)
    .where(where)
    .orderBy(desc(voiceStays.joinedAt))
    .limit(limit)
    .offset(offset)
    .all();
  const total = db().select({ total: count() }).from(voiceStays).where(where).get()?.total ?? 0;
  return { stays, total };
}

/** Marks every open stay as still running, so a crash loses at most one interval. */
export function heartbeat(now: Date): void {
  db().update(voiceStays).set({ lastSeenAt: now }).where(isNull(voiceStays.leftAt)).run();
}

/**
 * Matches the stored stays to who is in voice right now, for example after a restart. Stays of
 * members who are gone end at the last time the bot saw them. Members without a stay get one.
 */
export function reconcile(present: readonly Presence[], now: Date): void {
  const key = ({ guildId, channelId, userId }: Presence) => `${guildId}:${channelId}:${userId}`;
  const here = new Map(present.map((presence) => [key(presence), presence]));
  const open = db().select().from(voiceStays).where(isNull(voiceStays.leftAt)).all();
  const openKeys = new Set(open.map(key));
  db().transaction(() => {
    for (const stay of open.filter((stay) => !here.has(key(stay)))) {
      db()
        .update(voiceStays)
        .set({ leftAt: stay.lastSeenAt })
        .where(eq(voiceStays.id, stay.id))
        .run();
    }
    for (const presence of [...here.values()].filter((p) => !openKeys.has(key(p)))) {
      join(presence, now);
    }
  });
}

/** Deletes finished stays that ended before `before`. */
export function prune(before: Date): number {
  return db().delete(voiceStays).where(lt(voiceStays.leftAt, before)).run().changes;
}
