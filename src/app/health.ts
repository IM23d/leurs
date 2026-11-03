import { createServer } from "node:http";

import { logger } from "#shared/lib/logger.ts";

/**
 * Answers GET /health with 200 while the bot is connected to Discord and 503 otherwise, so Docker
 * and uptime monitors can tell when the bot is down. Returns a function that closes the server.
 */
export function startHealthServer(port: number, isReady: () => boolean): () => Promise<void> {
  const server = createServer((request, response) => {
    if (request.method !== "GET" || request.url !== "/health") {
      response.writeHead(404).end();
      return;
    }
    const ready = isReady();
    response
      .writeHead(ready ? 200 : 503, { "content-type": "application/json" })
      .end(JSON.stringify({ status: ready ? "ok" : "starting" }));
  });
  server.listen(port, () => {
    logger.info({ port }, "Health server is listening");
  });
  return () =>
    new Promise((resolve, reject) => {
      server.close((error) => {
        if (error) reject(error);
        else resolve();
      });
    });
}
