import { Events, PermissionFlagsBits, type GuildMember, type Message } from "discord.js";

import { defineEvent } from "#core/events.ts";
import { logger } from "#shared/lib/logger.ts";
import { errorEmbed, warningEmbed } from "#shared/ui/embeds.ts";

import { MAX_TIMEOUT_MS, recordAction } from "../actions.service.ts";
import { findBlockedTerm, type BlockedTerm, type Punishment } from "../blocked-terms.service.ts";
import { postLog } from "../mod-log.ts";
import { logEntryEmbed } from "../moderation.views.ts";
import { unbanTask } from "../tasks/unban.ts";

const PUNISHMENT_TEXT: Record<Punishment, { title: string; done: string }> = {
  warn: { title: "Warning", done: "warned" },
  mute: { title: "Mute", done: "muted" },
  kick: { title: "Kick", done: "kicked" },
  ban: { title: "Ban", done: "banned" },
};

const canPunish = (member: GuildMember, punishment: Punishment): boolean =>
  ({
    warn: true,
    mute: member.moderatable,
    kick: member.kickable,
    ban: member.bannable,
  })[punishment];

async function applyPunishment(member: GuildMember, term: BlockedTerm, reason: string) {
  const durationMs = term.durationMs ?? undefined;
  switch (term.punishment) {
    case "warn":
      return;
    case "mute":
      await member.timeout(Math.min(durationMs ?? MAX_TIMEOUT_MS, MAX_TIMEOUT_MS), reason);
      return;
    case "kick":
      await member.kick(reason);
      return;
    case "ban":
      await member.ban({ reason });
      if (durationMs !== undefined) {
        unbanTask.schedule(new Date(Date.now() + durationMs), {
          guildId: member.guild.id,
          userId: member.id,
        });
      }
  }
}

async function punish(message: Message<true>, member: GuildMember, term: BlockedTerm) {
  const { title, done } = PUNISHMENT_TEXT[term.punishment];
  const reason = `Used blocked term: ${term.term}`;
  const shown = term.customText ?? reason;
  if (!canPunish(member, term.punishment)) {
    const failure = errorEmbed(
      `I couldn't ${term.punishment} ${member.toString()}: my role is too low.`,
    );
    await postLog(message.guild, "blockedTermsLogChannelId", failure);
    return;
  }
  await applyPunishment(member, term, reason);
  recordAction({
    guildId: message.guildId,
    userId: member.id,
    moderatorId: null,
    action: term.punishment,
    reason,
    durationMs: term.durationMs ?? undefined,
  });
  const notice = warningEmbed(`${member.toString()}, you were ${done} for using a blocked term.`)
    .setTitle(title)
    .addFields({ name: "Reason", value: shown });
  await message.channel.send({ embeds: [notice] });
  const entry = logEntryEmbed({
    title,
    target: member.user,
    moderator: null,
    reason: shown,
    durationMs: term.durationMs ?? undefined,
    details: `In ${message.channel.toString()}`,
  });
  await postLog(message.guild, "blockedTermsLogChannelId", entry);
}

/** Deletes messages with a blocked term and punishes the sender. */
export const blockedTermsEvent = defineEvent({
  name: Events.MessageCreate,
  run: async (message) => {
    if (message.author.bot || !message.inGuild() || message.content === "") return;
    const term = findBlockedTerm(message.guildId, message.content);
    if (!term) return;
    const member =
      message.member ?? (await message.guild.members.fetch(message.author.id).catch(() => null));
    // Moderators are exempt, so they can type a term while blocking or unblocking it.
    if (!member || member.permissions.has(PermissionFlagsBits.ManageMessages)) return;
    await message.delete().catch(() => undefined);
    await punish(message, member, term).catch(async (error: unknown) => {
      logger.warn({ err: error, guildId: message.guildId }, "Blocked term punishment failed");
      const failure = errorEmbed(`I couldn't ${term.punishment} ${member.toString()}.`);
      await postLog(message.guild, "blockedTermsLogChannelId", failure);
    });
  },
});
