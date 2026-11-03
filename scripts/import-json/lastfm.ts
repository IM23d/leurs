import { z } from "zod";

import { linkAccount } from "#modules/lastfm/lastfm.service.ts";

import type { Importer } from "./source.ts";

// lastfm.json: { "<userId>": "<Last.fm username>" }
const accounts = z.record(z.string(), z.string().min(1));

export const lastfmImporter: Importer = {
  name: "lastfm",
  run: (source) => {
    const data = accounts.optional().parse(source.read("lastfm.json")) ?? {};
    return Object.entries(data).map(([userId, username]) => {
      linkAccount(userId, username);
    }).length;
  },
};
