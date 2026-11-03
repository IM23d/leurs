import { z } from "zod";

import { MAX_TERM_LENGTH, setAutoReaction } from "#modules/tools/auto-reactions.service.ts";
import { parseEmoji } from "#shared/lib/emoji.ts";

import type { Importer } from "./source.ts";

// auto_reactions.json: { "<guildId>": { "<term>": "<emoji>" } }
const guilds = z.record(z.string(), z.record(z.string(), z.unknown()).catch({}));

const autoReaction = z.object({
  guildId: z.string().regex(/^\d{17,20}$/),
  term: z.string().trim().min(1).max(MAX_TERM_LENGTH),
  emoji: z
    .string()
    .trim()
    .refine((text) => parseEmoji(text) !== undefined),
});

export const toolsImporter: Importer = {
  name: "tools",
  run: (source) => {
    const data = guilds.optional().parse(source.read("auto_reactions.json")) ?? {};
    const results = Object.entries(data).flatMap(([guildId, terms]) =>
      Object.entries(terms).map(([term, emoji]) =>
        autoReaction.safeParse({ guildId, term, emoji }),
      ),
    );
    const valid = results.flatMap((result) => (result.success ? [result.data] : []));
    valid.forEach(({ guildId, term, emoji }) => setAutoReaction(guildId, term, emoji));
    const skipped = results.length - valid.length;
    if (skipped > 0) console.warn(`tools: skipped ${skipped} malformed auto reactions`);
    return valid.length;
  },
};
