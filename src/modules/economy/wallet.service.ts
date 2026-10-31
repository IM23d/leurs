import { and, eq, gte, inArray, sql } from "drizzle-orm";

import { db } from "#db/client.ts";
import { chunks } from "#shared/lib/chunks.ts";

import { balances } from "./economy.schema.ts";

/** What a new account starts with, like the old bot. */
export const STARTING_BALANCE = 50;
const MAX_BEG = 100;

export type Random = () => number;

/** A user without an account reads as the starting balance. */
export function getBalance(userId: string): number {
  const row = db().select().from(balances).where(eq(balances.userId, userId)).get();
  return row?.balance ?? STARTING_BALANCE;
}

function openAccount(userId: string): void {
  db().insert(balances).values({ userId, balance: STARTING_BALANCE }).onConflictDoNothing().run();
}

/** Adds coins and returns the new balance. */
export function addBalance(userId: string, amount: number): number {
  return db()
    .insert(balances)
    .values({ userId, balance: STARTING_BALANCE + amount })
    .onConflictDoUpdate({
      target: balances.userId,
      set: { balance: sql`${balances.balance} + ${amount}` },
    })
    .returning()
    .get().balance;
}

/** Takes coins if the user has enough. Returns the new balance, or undefined when short. */
export function takeBalance(userId: string, amount: number): number | undefined {
  openAccount(userId);
  return db()
    .update(balances)
    .set({ balance: sql`${balances.balance} - ${amount}` })
    .where(and(eq(balances.userId, userId), gte(balances.balance, amount)))
    .returning()
    .all()
    .at(0)?.balance;
}

/** Takes up to `amount` coins, stopping at zero. Returns how many were taken and the balance. */
export function takeUpTo(userId: string, amount: number): { taken: number; balance: number } {
  return db().transaction(() => {
    const before = getBalance(userId);
    openAccount(userId);
    const balance = db()
      .update(balances)
      .set({ balance: sql`max(${balances.balance} - ${amount}, 0)` })
      .where(eq(balances.userId, userId))
      .returning()
      .get().balance;
    return { taken: before - balance, balance };
  });
}

/** Pays 0 to 100 coins, like the old bot. */
export function beg(
  userId: string,
  random: Random = Math.random,
): { earned: number; balance: number } {
  const earned = Math.floor(random() * (MAX_BEG + 1));
  return { earned, balance: addBalance(userId, earned) };
}

/** Balances of the given users that have an account, richest first. */
export function balanceRanking(userIds: readonly string[]): { userId: string; balance: number }[] {
  return chunks(userIds)
    .flatMap((ids) =>
      db()
        .select({ userId: balances.userId, balance: balances.balance })
        .from(balances)
        .where(inArray(balances.userId, ids))
        .all(),
    )
    .toSorted((a, b) => b.balance - a.balance || a.userId.localeCompare(b.userId));
}
