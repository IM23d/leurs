import { defineCommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";
import { embed } from "#shared/ui/embeds.ts";

const DOCS_URL = "https://docs.leurs.ch";

export const helpCommand = defineCommand({
  name: "help",
  description: "List commands or show how to use one",
  options: { command: opt.string("A command name").optional() },
  run: async (ctx, { command: name }) => {
    if (name === undefined) {
      const list = ctx.commands
        .filter((command) => !command.ownerOnly)
        .map((command) => `\`${ctx.prefix}${command.name}\` ${command.description}`)
        .join("\n");
      await ctx.reply(
        embed(list)
          .setTitle("Commands")
          .setFooter({
            text: `Every command works with / and with ${ctx.prefix === "/" ? "the server prefix" : ctx.prefix}. Full docs: ${DOCS_URL}`,
          }),
      );
      return;
    }
    const command = ctx.commands.find((candidate) => candidate.name === name.toLowerCase());
    if (!command) throw new UserError(`There is no command called \`${name}\`.`);
    const lines = [...command.leaves].map(([sub, leaf]) => {
      const path = sub === "" ? command.name : `${command.name} ${sub}`;
      const aliases =
        leaf.aliases.length > 0 ? ` (also ${leaf.aliases.map((a) => `\`${a}\``).join(", ")})` : "";
      return `\`${ctx.prefix}${path}\` ${leaf.description}${aliases}`;
    });
    await ctx.reply(
      embed(lines.join("\n")).setTitle(`${ctx.prefix}${command.name}`).setURL(DOCS_URL),
    );
  },
});
