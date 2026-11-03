import { randomBytes } from "node:crypto";

import { logger } from "#shared/lib/logger.ts";
import { errorEmbed } from "#shared/ui/embeds.ts";

import { UserError } from "../errors.ts";

/** Turns an error into the text the user sees. Unexpected errors are logged with a reference. */
function describeFailure(error: unknown, context: Record<string, unknown>): string {
  if (error instanceof UserError) return error.message;
  const reference = randomBytes(4).toString("hex");
  logger.error({ err: error, reference, ...context }, "Command failed");
  return `Something went wrong. If it keeps happening, report reference \`${reference}\`.`;
}

export const failureEmbed = (error: unknown, context: Record<string, unknown>) =>
  errorEmbed(describeFailure(error, context));
