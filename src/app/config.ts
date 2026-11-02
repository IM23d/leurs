import { z } from "zod";

const optional = z
  .string()
  .optional()
  .transform((value) => (value === "" ? undefined : value));

const schema = z.object({
  DISCORD_TOKEN: z.string().min(1),
  DISCORD_CLIENT_ID: z.string().min(1),
  DEV_GUILD_ID: optional,
  OWNER_IDS: z
    .string()
    .default("")
    .transform((value) =>
      value
        .split(",")
        .map((id) => id.trim())
        .filter(Boolean),
    ),
  DATABASE_PATH: z.string().default("data/leurs.db"),
  HEALTH_PORT: z.coerce.number().int().min(1).max(65_535).default(9992),
  LASTFM_API_KEY: optional,
  DEEPSEEK_API_KEY: optional,
  GOOGLE_API_KEY: optional,
  GOOGLE_CSE_ID: optional,
  LOG_LEVEL: z.enum(["trace", "debug", "info", "warn", "error", "fatal"]).default("info"),
});

export type Config = z.infer<typeof schema>;

let current: Config | undefined;

/** Parses the environment once. Throws with every missing or invalid variable listed. */
export function loadConfig(env: NodeJS.ProcessEnv = process.env): Config {
  const result = schema.safeParse(env);
  if (!result.success) {
    const problems = result.error.issues.map(
      (issue) => `  ${issue.path.join(".")}: ${issue.message}`,
    );
    throw new Error(
      `Invalid configuration. Check your .env file or environment:\n${problems.join("\n")}`,
    );
  }
  current = result.data;
  return current;
}

export function config(): Config {
  if (!current) throw new Error("loadConfig() must run before config() is used");
  return current;
}
