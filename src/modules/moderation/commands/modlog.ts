import { PermissionFlagsBits } from "discord.js";

import { defineCommand } from "#core/commands/define.ts";
import { definePaginator } from "#shared/ui/paginator.ts";

import { countActions, listActions } from "../actions.service.ts";
import { modlogEmbed } from "../moderation.views.ts";
import { anyUser } from "../options.ts";

export const modlogPaginator = definePaginator({
  id: "modlog",
  render: async ({ guild, page, args: [userId = ""] }) => {
    const user = await guild.client.users.fetch(userId);
    const member = await guild.members.fetch(userId).catch(() => undefined);
    const actions = listActions(guild.id, userId);
    return modlogEmbed(user, member, actions, countActions(actions), page);
  },
});

export const modlogCommand = defineCommand({
  name: "modlog",
  description: "Show a member's warnings, bans, mutes and other actions",
  aliases: ["overview", "o"],
  permissions: PermissionFlagsBits.ModerateMembers,
  options: { user: anyUser("Whose history") },
  run: (ctx, { user }) => modlogPaginator.reply(ctx, { args: [user.id] }),
});
