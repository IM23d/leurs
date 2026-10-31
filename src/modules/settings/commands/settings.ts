import { ChannelType, PermissionFlagsBits } from "discord.js";

import { defineCommand, subcommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { UserError } from "#core/errors.ts";
import { embed, successEmbed } from "#shared/ui/embeds.ts";

import {
  getPrefix,
  getSettings,
  updateSettings,
  type ChannelSetting,
  type RoleSetting,
} from "../settings.service.ts";

const CHANNEL_SETTINGS = {
  "mod-log": { key: "modLogChannelId", label: "Moderation log" },
  "blocked-terms-log": { key: "blockedTermsLogChannelId", label: "Blocked terms log" },
  "level-up": { key: "levelUpChannelId", label: "Level-up messages" },
} as const satisfies Record<string, { key: ChannelSetting; label: string }>;

const ROLE_SETTINGS = {
  jail: { key: "jailRoleId", label: "Jail role" },
} as const satisfies Record<string, { key: RoleSetting; label: string }>;

const choicesOf = (settings: Record<string, { label: string }>) =>
  Object.entries(settings).map(([value, { label }]) => ({ name: label, value }));

const lookup = <T>(settings: Record<string, T>, name: string): T => {
  const found = settings[name];
  if (!found) throw new UserError(`\`${name}\` is not a setting.`);
  return found;
};

export const settingsCommand = defineCommand({
  name: "settings",
  description: "View and change this server's bot settings",
  permissions: PermissionFlagsBits.Administrator,
  defaultSubcommand: "view",
  subcommands: {
    view: subcommand({
      description: "Show the current settings",
      run: async (ctx) => {
        const settings = getSettings(ctx.guild.id);
        const show = (id: string | null, mention: (id: string) => string) =>
          id === null ? "Not set" : mention(id);
        const lines = [
          `**Prefix**: \`${getPrefix(ctx.guild.id)}\``,
          ...Object.values(CHANNEL_SETTINGS).map(
            ({ key, label }) => `**${label}**: ${show(settings[key], (id) => `<#${id}>`)}`,
          ),
          ...Object.values(ROLE_SETTINGS).map(
            ({ key, label }) => `**${label}**: ${show(settings[key], (id) => `<@&${id}>`)}`,
          ),
        ];
        await ctx.reply(embed(lines.join("\n")).setTitle("Server settings"));
      },
    }),
    channel: subcommand({
      description: "Set or clear a channel setting",
      options: {
        setting: opt.string("Which setting").choices(choicesOf(CHANNEL_SETTINGS)),
        channel: opt.channel("Leave empty to clear").optional(),
      },
      run: async (ctx, { setting, channel }) => {
        const { key, label } = lookup(CHANNEL_SETTINGS, setting);
        if (channel && channel.type !== ChannelType.GuildText) {
          throw new UserError("Pick a text channel.");
        }
        updateSettings(ctx.guild.id, { [key]: channel?.id ?? null });
        await ctx.reply(successEmbed(`${label}: ${channel ? `<#${channel.id}>` : "cleared"}.`));
      },
    }),
    role: subcommand({
      description: "Set or clear a role setting",
      options: {
        setting: opt.string("Which setting").choices(choicesOf(ROLE_SETTINGS)),
        role: opt.role("Leave empty to clear").optional(),
      },
      run: async (ctx, { setting, role }) => {
        const { key, label } = lookup(ROLE_SETTINGS, setting);
        updateSettings(ctx.guild.id, { [key]: role?.id ?? null });
        await ctx.reply(successEmbed(`${label}: ${role ? `<@&${role.id}>` : "cleared"}.`));
      },
    }),
  },
});
