import { z } from "zod";

import { importStats } from "#modules/levels/levels.service.ts";

import type { Importer } from "./source.ts";

// levels.json: { "<userId>": { "xp", "level", "total_messages", "last_message" } }
// The level is derived from xp now, and last_message was never read, so both are dropped.
const levelsFile = z.record(
  z.string(),
  z.object({ xp: z.number().int().min(0), total_messages: z.number().int().min(0) }),
);

// voice_levels.json: { "<userId>": { "voice_time": <seconds, fractional> } }
const voiceFile = z.record(z.string(), z.object({ voice_time: z.number().min(0).default(0) }));

export const levelsImporter: Importer = {
  name: "levels",
  run: (source) => {
    const levels = levelsFile.optional().parse(source.read("levels.json")) ?? {};
    const voice = voiceFile.optional().parse(source.read("voice_levels.json")) ?? {};
    const userIds = new Set([...Object.keys(levels), ...Object.keys(voice)]);
    return importStats(
      [...userIds].map((userId) => ({
        userId,
        xp: levels[userId]?.xp ?? 0,
        messages: levels[userId]?.total_messages ?? 0,
        voiceSeconds: Math.floor(voice[userId]?.voice_time ?? 0),
      })),
    );
  },
};
