import { mkdirSync } from "node:fs";
import { dirname } from "node:path";

import SQLite from "better-sqlite3";
import { drizzle, type BetterSQLite3Database } from "drizzle-orm/better-sqlite3";
import { migrate } from "drizzle-orm/better-sqlite3/migrator";

export type Db = BetterSQLite3Database;

let current: Db | undefined;

/** Opens the database file, applies pending migrations and makes it available through db(). */
export function openDb(path: string, migrationsFolder = "drizzle"): Db {
  if (path !== ":memory:") mkdirSync(dirname(path), { recursive: true });
  const sqlite = new SQLite(path);
  sqlite.pragma("journal_mode = WAL");
  sqlite.pragma("foreign_keys = ON");
  current = drizzle(sqlite);
  migrate(current, { migrationsFolder });
  return current;
}

/** Replaces the active database. Used by tests. */
export function setDb(next: Db): void {
  current = next;
}

export function db(): Db {
  if (!current) throw new Error("openDb() must run before db() is used");
  return current;
}
