import { eq } from "drizzle-orm";

import { db } from "#db/client.ts";

import { lastfmAccounts, type LastfmAccount } from "./lastfm.schema.ts";

export function linkAccount(userId: string, username: string): void {
  db()
    .insert(lastfmAccounts)
    .values({ userId, username })
    .onConflictDoUpdate({ target: lastfmAccounts.userId, set: { username } })
    .run();
}

/** Returns false when the user had no linked account. */
export function unlinkAccount(userId: string): boolean {
  return (
    db().delete(lastfmAccounts).where(eq(lastfmAccounts.userId, userId)).returning().all().length >
    0
  );
}

export function getUsername(userId: string): string | undefined {
  return db().select().from(lastfmAccounts).where(eq(lastfmAccounts.userId, userId)).get()
    ?.username;
}

export function allAccounts(): LastfmAccount[] {
  return db().select().from(lastfmAccounts).orderBy(lastfmAccounts.username).all();
}
