import { defineCommand, subcommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";
import { memberIds } from "#shared/lib/members.ts";
import { settleLimited } from "#shared/lib/settle-limited.ts";
import { successEmbed } from "#shared/ui/embeds.ts";

import { fetchProfile, fetchRecent, requireLastfm } from "../lastfm-client.ts";
import { allAccounts, linkAccount, unlinkAccount } from "../lastfm.service.ts";
import { profileEmbed, serverEmbed, type Listener } from "../lastfm.views.ts";
import { linkedUsername } from "../linked-username.ts";

const MAX_USERNAME_LENGTH = 15;
const MAX_PARALLEL_REQUESTS = 4;

export const lastfmCommand = defineCommand({
  name: "lastfm",
  description: "Link your Last.fm account and show your profile",
  defaultSubcommand: "profile",
  subcommands: {
    link: subcommand({
      description: "Link your Last.fm account",
      aliases: ["login"],
      options: { username: opt.string("Your Last.fm username").max(MAX_USERNAME_LENGTH) },
      run: async (ctx, { username }) => {
        requireLastfm();
        await ctx.defer();
        const profile = await fetchProfile(username);
        linkAccount(ctx.user.id, profile.username);
        await ctx.reply(successEmbed(`Linked Last.fm account \`${profile.username}\`.`));
      },
    }),
    unlink: subcommand({
      description: "Unlink your Last.fm account",
      aliases: ["logout"],
      run: async (ctx) => {
        if (!unlinkAccount(ctx.user.id)) throw new UserError("You don't have Last.fm linked.");
        await ctx.reply(successEmbed("Unlinked your Last.fm account."));
      },
    }),
    profile: subcommand({
      description: "Show a Last.fm profile",
      aliases: ["lf", "profile", "me", "p"],
      options: { user: opt.user("Whose profile").optional() },
      run: async (ctx, { user = ctx.user }) => {
        requireLastfm();
        const username = linkedUsername(user.id, ctx.user.id, ctx.prefix);
        await ctx.defer();
        const [profile, recent] = await Promise.all([
          fetchProfile(username),
          fetchRecent(username),
        ]);
        await ctx.reply(profileEmbed(profile, recent, user));
      },
    }),
    server: subcommand({
      description: "Show what members of this server are playing",
      aliases: ["servernowplaying", "snp"],
      run: async (ctx) => {
        requireLastfm();
        await ctx.defer();
        const members = await memberIds(ctx.guild);
        const accounts = allAccounts().filter((account) => members.has(account.userId));
        const results = await settleLimited(
          accounts,
          MAX_PARALLEL_REQUESTS,
          async ({ username }) => ({
            username,
            recent: await fetchRecent(username),
          }),
        );
        const listeners = results
          .flatMap((result) => (result.status === "fulfilled" ? [result.value] : []))
          .flatMap(({ username, recent: { track } }): Listener[] =>
            track?.nowPlaying ? [{ username, track }] : [],
          );
        await ctx.reply(serverEmbed(listeners, accounts.length));
      },
    }),
  },
});
