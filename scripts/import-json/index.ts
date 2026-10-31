// One-time import of the Python bot's JSON files into SQLite.
// Usage: npm run import:json -- <path to the old data/ folder>
// Run it against a fresh database. Each importer runs in its own transaction.
import { loadConfig } from "#app/config.ts";
import { openDb } from "#db/client.ts";

import { settingsImporter } from "./settings.ts";
import { legacySource, type Importer } from "./source.ts";

const importers: readonly Importer[] = [settingsImporter];

const directory = process.argv[2];
if (!directory) {
  console.error("Usage: npm run import:json -- <path to the old data/ folder>");
  process.exit(1);
}

const config = loadConfig();
const db = openDb(config.DATABASE_PATH);
const source = legacySource(directory);

for (const importer of importers) {
  const rows = db.transaction(() => importer.run(source));
  console.log(`${importer.name}: ${rows} rows`);
}
