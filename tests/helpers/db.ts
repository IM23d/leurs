import { globSync } from "node:fs";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

import SQLite from "better-sqlite3";
import { generateSQLiteDrizzleJson, generateSQLiteMigration } from "drizzle-kit/api";
import { drizzle } from "drizzle-orm/better-sqlite3";
import { beforeEach } from "vitest";

import { setDb, type Db } from "#db/client.ts";

const schemaFiles = globSync("src/**/*.schema.ts").map((file) => pathToFileURL(resolve(file)).href);

async function createSchemaSql(): Promise<string[]> {
  const modules = await Promise.all(
    schemaFiles.map((file) => import(file) as Promise<Record<string, unknown>>),
  );
  const schema = Object.assign({}, ...modules) as Record<string, unknown>;
  // drizzle-kit's API typings do not resolve under the lint program, so the value reads as an error type.
  // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
  const empty = await generateSQLiteDrizzleJson({});
  return generateSQLiteMigration(empty, await generateSQLiteDrizzleJson(schema));
}

const schemaSql = createSchemaSql();

/** Gives each test a fresh in-memory database built from every *.schema.ts file. */
export function useTestDb(): () => Db {
  let current: Db | undefined;
  beforeEach(async () => {
    const sqlite = new SQLite(":memory:");
    for (const statement of await schemaSql) sqlite.exec(statement);
    current = drizzle(sqlite);
    setDb(current);
  });
  return () => {
    if (!current) throw new Error("useTestDb() database is used outside a test");
    return current;
  };
}
