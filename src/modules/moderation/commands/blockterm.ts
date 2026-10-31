import { PermissionFlagsBits } from "discord.js";

import { defineCommand, subcommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";
import { successEmbed } from "#shared/ui/embeds.ts";
import { definePaginator } from "#shared/ui/paginator.ts";

import { blockTerm, listTerms, PUNISHMENTS, unblockTerm } from "../blocked-terms.service.ts";
import { blockedTermsEmbed, describePunishment } from "../moderation.views.ts";
import { durationOrPermanent } from "../options.ts";

const MAX_TERM_LENGTH = 100;

export const blockedTermsPaginator = definePaginator({
  id: "blocked-terms",
  render: ({ guild, page }) => blockedTermsEmbed(listTerms(guild.id), page),
});

export const blocktermCommand = defineCommand({
  name: "blockterm",
  description: "Delete messages with a term and punish whoever sends it",
  permissions: PermissionFlagsBits.ManageMessages,
  defaultSubcommand: "add",
  subcommands: {
    add: subcommand({
      description: "Block a term, or change how a blocked term is punished",
      options: {
        term: opt
          .string("The word or phrase. Use quotes for more than one word")
          .max(MAX_TERM_LENGTH),
        punishment: opt
          .string("What happens to whoever sends it")
          .choices(PUNISHMENTS.map((value) => ({ name: value, value }))),
        duration: durationOrPermanent("How long a mute or ban lasts, e.g. 10m or 7d").optional(),
        advanced: opt.boolean("Also catch accents, digits and repeated letters").optional(),
        message: opt.string("What to tell the member instead of the default").rest().optional(),
      },
      run: async (ctx, { term, punishment, duration, advanced = false, message }) => {
        const punishmentType = PUNISHMENTS.find((value) => value === punishment.toLowerCase());
        if (!punishmentType) throw new UserError("Pick warn, mute, kick or ban.");
        const row = blockTerm({
          guildId: ctx.guild.id,
          term,
          punishment: punishmentType,
          durationMs: duration ?? undefined,
          customText: message,
          advanced,
          addedById: ctx.user.id,
        });
        await ctx.reply(
          successEmbed(`Blocked \`${row.term}\`.`).addFields(
            { name: "Punishment", value: describePunishment(row), inline: true },
            { name: "Filtering", value: row.advanced ? "Advanced" : "Basic", inline: true },
            ...(row.customText === null ? [] : [{ name: "Message", value: row.customText }]),
          ),
        );
      },
    }),
    remove: subcommand({
      description: "Unblock a term",
      aliases: ["unblockterm"],
      options: { term: opt.string("The blocked term").rest() },
      run: async (ctx, { term }) => {
        if (!unblockTerm(ctx.guild.id, term)) throw new UserError(`\`${term}\` is not blocked.`);
        await ctx.reply(successEmbed(`Unblocked \`${term}\`.`));
      },
    }),
    list: subcommand({
      description: "List the blocked terms",
      aliases: ["blockedterms"],
      options: { page: opt.integer("Page").min(1).optional() },
      run: (ctx, { page }) => blockedTermsPaginator.reply(ctx, { page: page ?? 1 }),
    }),
  },
});
