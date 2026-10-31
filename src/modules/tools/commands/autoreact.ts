import { PermissionFlagsBits } from "discord.js";

import { defineCommand, subcommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";
import { parseEmoji } from "#shared/lib/emoji.ts";
import { embed, successEmbed } from "#shared/ui/embeds.ts";
import { definePaginator, paginate } from "#shared/ui/paginator.ts";

import {
  listAutoReactions,
  MAX_TERM_LENGTH,
  removeAutoReaction,
  setAutoReaction,
} from "../auto-reactions.service.ts";

const PAGE_SIZE = 15;

export const autoReactList = definePaginator({
  id: "autoreact-list",
  render: ({ guild, page }) => {
    const all = listAutoReactions(guild.id);
    const { items, page: current, pageCount } = paginate(all, page, PAGE_SIZE);
    const lines = items.map(({ term, emoji }) => `${emoji} \`${term}\``);
    const shown =
      all.length === 0
        ? embed("No auto reactions yet. Add one with `/autoreact add`.")
        : embed(lines.join("\n")).setFooter({ text: `Page ${current} of ${pageCount}` });
    return { embed: shown.setTitle("Auto reactions"), pageCount };
  },
});

export const autoreactCommand = defineCommand({
  name: "autoreact",
  description: "React to messages that contain a word",
  permissions: PermissionFlagsBits.Administrator,
  subcommands: {
    add: subcommand({
      description: "React with an emoji when a message contains a term",
      aliases: ["reaction"],
      options: {
        term: opt.string("The word or phrase, any case").max(MAX_TERM_LENGTH),
        emoji: opt.string("The emoji to react with"),
      },
      run: async (ctx, { term, emoji }) => {
        const parsed = parseEmoji(emoji);
        if (!parsed) throw new UserError(`\`${emoji}\` is not an emoji.`);
        if (parsed.customId && !ctx.client.emojis.cache.has(parsed.customId)) {
          throw new UserError("I can only use emojis from servers I'm in.");
        }
        const added = setAutoReaction(ctx.guild.id, term, parsed.text);
        await ctx.reply(
          successEmbed(
            `I'll react with ${added.emoji} to messages that contain \`${added.term}\`.`,
          ),
        );
      },
    }),
    remove: subcommand({
      description: "Stop reacting to a term",
      aliases: ["reactionremove", "reaction remove"],
      options: { term: opt.string("The term to remove").rest() },
      run: async (ctx, { term }) => {
        const removed = removeAutoReaction(ctx.guild.id, term);
        if (!removed) throw new UserError(`No auto reaction for \`${term}\`.`);
        await ctx.reply(
          successEmbed(`Removed the auto reaction ${removed.emoji} for \`${removed.term}\`.`),
        );
      },
    }),
    list: subcommand({
      description: "Show every auto reaction",
      aliases: ["reaction list"],
      run: (ctx) => autoReactList.reply(ctx),
    }),
  },
});
