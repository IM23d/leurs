import { defineCommand } from "#core/commands/define.ts";
import { findHelpTarget, helpFor } from "#core/commands/help.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";
import { getPrefix } from "#modules/settings/api.ts";
import { embed } from "#shared/ui/embeds.ts";

const DOCS_URL = "https://docs.leurs.ch";

export const helpCommand = defineCommand({
  name: "help",
  description: "List commands or show how to use one",
  options: { command: opt.string("A command or subcommand, e.g. bday set").rest().optional() },
  run: async (ctx, { command: name }) => {
    const prefixes = { prefix: ctx.prefix, textPrefix: getPrefix(ctx.guild.id) };
    if (name === undefined) {
      const list = ctx.commands
        .filter((command) => !command.ownerOnly)
        .map((command) => `\`${ctx.prefix}${command.name}\` ${command.description}`)
        .join("\n");
      await ctx.reply(
        embed(list)
          .setTitle("Commands")
          .setFooter({
            text: `Add --help to any command for details, e.g. ${prefixes.textPrefix}bday --help. Every command also works with /. Docs: ${DOCS_URL}`,
          }),
      );
      return;
    }
    const target = findHelpTarget(ctx.commands, name);
    if (!target) throw new UserError(`There is no command called \`${name}\`.`);
    await ctx.reply(helpFor(target, prefixes));
  },
});
