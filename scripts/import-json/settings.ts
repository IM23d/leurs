import { z } from "zod";

import { updateSettings } from "#modules/settings/settings.service.ts";

import type { Importer } from "./source.ts";

// prefix.json: { "<guildId>": "<prefix>" }
const prefixes = z.record(z.string(), z.string());

export const settingsImporter: Importer = {
  name: "settings",
  run: (source) => {
    const data = prefixes.optional().parse(source.read("prefix.json")) ?? {};
    return Object.entries(data).map(([guildId, prefix]) => updateSettings(guildId, { prefix }))
      .length;
  },
};
