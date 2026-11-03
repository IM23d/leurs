import { startBot } from "#app/bot.ts";
import { loadConfig } from "#app/config.ts";
import { openDb } from "#db/client.ts";
import { logger } from "#shared/lib/logger.ts";

const config = loadConfig();
openDb(config.DATABASE_PATH);
const stop = await startBot(config);

for (const signal of ["SIGINT", "SIGTERM"] as const) {
  process.once(signal, () => {
    logger.info({ signal }, "Shutting down");
    stop()
      .then(() => process.exit(0))
      .catch((error: unknown) => {
        logger.error({ err: error }, "Shutdown failed");
        process.exit(1);
      });
  });
}
