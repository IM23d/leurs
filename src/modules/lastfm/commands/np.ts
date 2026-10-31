import { defineCommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";

import { fetchPlays, fetchRecent, requireLastfm } from "../lastfm-client.ts";
import { notPlayingEmbed, nowPlayingEmbed } from "../lastfm.views.ts";
import { linkedUsername } from "../linked-username.ts";

export const npCommand = defineCommand({
  name: "np",
  description: "Show what you or a member is playing on Last.fm",
  options: { user: opt.user("Whose track").optional() },
  run: async (ctx, { user = ctx.user }) => {
    requireLastfm();
    const username = linkedUsername(user.id, ctx.user.id, ctx.prefix);
    await ctx.defer();
    const recent = await fetchRecent(username);
    const { track } = recent;
    if (!track?.nowPlaying) {
      await ctx.reply(notPlayingEmbed(username, user));
      return;
    }
    const plays = await fetchPlays(username, track);
    await ctx.reply(nowPlayingEmbed(username, user, { ...recent, track }, plays));
  },
});
