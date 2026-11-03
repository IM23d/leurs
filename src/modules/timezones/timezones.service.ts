import { eq } from "drizzle-orm";

import { db } from "#db/client.ts";

import { timezones } from "./timezones.schema.ts";

/** The zone used for users who have not set one. */
const DEFAULT_ZONE = "UTC";

export interface TimezoneSettings {
  readonly zone: string | undefined;
  readonly use24Hour: boolean;
}

export function getTimezoneSettings(userId: string): TimezoneSettings {
  const row = db().select().from(timezones).where(eq(timezones.userId, userId)).get();
  return { zone: row?.zone ?? undefined, use24Hour: row?.use24Hour ?? false };
}

/** The user's zone, or UTC when they have not set one. */
export const zoneFor = (userId: string): string => getTimezoneSettings(userId).zone ?? DEFAULT_ZONE;

function upsert(userId: string, changes: { zone?: string; use24Hour?: boolean }): void {
  db()
    .insert(timezones)
    .values({ userId, ...changes })
    .onConflictDoUpdate({ target: timezones.userId, set: changes })
    .run();
}

export const setZone = (userId: string, zone: string): void => {
  upsert(userId, { zone });
};

export const setUse24Hour = (userId: string, use24Hour: boolean): void => {
  upsert(userId, { use24Hour });
};
