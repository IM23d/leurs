import {
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle,
  MessageFlags,
  type EmbedBuilder,
  type Guild,
} from "discord.js";

import type { CommandContext } from "#core/commands/context.ts";
import { customId, defineComponent, type Component } from "#core/components.ts";

import { errorEmbed } from "./embeds.ts";

export interface Page<T> {
  readonly items: readonly T[];
  readonly page: number;
  readonly pageCount: number;
  /** Index of the first item on this page in the full list. */
  readonly offset: number;
}

/** Cuts one page out of a list. Clamps `page` to the pages that exist. */
export function paginate<T>(items: readonly T[], page: number, pageSize: number): Page<T> {
  const pageCount = Math.max(1, Math.ceil(items.length / pageSize));
  const current = Math.min(Math.max(1, page), pageCount);
  const offset = (current - 1) * pageSize;
  return { items: items.slice(offset, offset + pageSize), page: current, pageCount, offset };
}

interface RenderInput {
  readonly guild: Guild;
  readonly page: number;
  readonly args: readonly string[];
}

interface Rendered {
  readonly embed: EmbedBuilder;
  readonly pageCount: number;
}

export interface Paginator {
  readonly component: Component;
  /** Sends page `page` with previous and next buttons that only the caller can use. */
  reply(ctx: CommandContext, options?: { page?: number; args?: readonly string[] }): Promise<void>;
}

/**
 * A paged embed with previous and next buttons. The page and arguments live in the button IDs,
 * so the buttons keep working after a restart. Register `component` in the module.
 */
export function definePaginator(definition: {
  id: string;
  render: (input: RenderInput) => Rendered | Promise<Rendered>;
}): Paginator {
  const buttons = (page: number, pageCount: number, ownerId: string, args: readonly string[]) =>
    new ActionRowBuilder<ButtonBuilder>().addComponents(
      new ButtonBuilder()
        .setCustomId(customId(component, page - 1, ownerId, ...args))
        .setLabel("Previous")
        .setStyle(ButtonStyle.Secondary)
        .setDisabled(page <= 1),
      new ButtonBuilder()
        .setCustomId(customId(component, page + 1, ownerId, ...args))
        .setLabel("Next")
        .setStyle(ButtonStyle.Secondary)
        .setDisabled(page >= pageCount),
    );

  const view = async (guild: Guild, page: number, ownerId: string, args: readonly string[]) => {
    const rendered = await definition.render({ guild, page, args });
    const current = Math.min(Math.max(1, page), rendered.pageCount);
    const components =
      rendered.pageCount > 1 ? [buttons(current, rendered.pageCount, ownerId, args)] : [];
    return { embeds: [rendered.embed], components };
  };

  const component = defineComponent({
    id: definition.id,
    run: async (interaction, [page = "1", ownerId = "", ...args]) => {
      if (!interaction.isButton()) return;
      if (interaction.user.id !== ownerId) {
        await interaction.reply({
          embeds: [errorEmbed("Only the person who ran the command can change pages.")],
          flags: MessageFlags.Ephemeral,
        });
        return;
      }
      await interaction.update(await view(interaction.guild, Number(page), ownerId, args));
    },
  });

  return {
    component,
    reply: async (ctx, { page = 1, args = [] } = {}) => {
      await ctx.reply(await view(ctx.guild, page, ctx.user.id, args));
    },
  };
}
