import { time, TimestampStyles, type EmbedBuilder, type GuildMember, type User } from "discord.js";

import { formatDuration } from "#shared/lib/duration.ts";
import { colors, embed } from "#shared/ui/embeds.ts";
import { paginate } from "#shared/ui/paginator.ts";

import type { BlockedTerm, ModAction } from "./moderation.schema.ts";

export const NO_REASON = "No reason given";
const ACTIONS_PER_PAGE = 5;
const TERMS_PER_PAGE = 10;

const capitalize = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);

export interface LogEntry {
  readonly title: string;
  /** Who it was done to. Purges have no target. */
  readonly target?: User;
  /** Null for automod. */
  readonly moderator: User | null;
  readonly reason?: string | undefined;
  readonly durationMs?: number | undefined;
  readonly details?: string;
}

const LOG_COLORS: Record<string, number> = {
  Warning: colors.warning,
  Unmute: colors.success,
  Unjail: colors.success,
  Unban: colors.success,
  Purge: colors.brand,
};

export function logEntryEmbed(entry: LogEntry): EmbedBuilder {
  const fields = [
    entry.target && { name: "Member", value: `${entry.target.toString()} (${entry.target.tag})` },
    { name: "Moderator", value: entry.moderator?.toString() ?? "Automod" },
    entry.durationMs !== undefined && {
      name: "Duration",
      value: formatDuration(entry.durationMs),
    },
    entry.reason !== undefined && { name: "Reason", value: entry.reason },
  ].filter((field) => typeof field === "object");
  return embed(entry.details)
    .setTitle(entry.title)
    .setColor(LOG_COLORS[entry.title] ?? colors.error)
    .addFields(fields.map((field) => ({ ...field, inline: field.name !== "Reason" })))
    .setTimestamp();
}

const ACTION_LABELS: Record<string, string> = { warn: "Warnings" };
const pluralLabel = (action: string) => ACTION_LABELS[action] ?? `${capitalize(action)}s`;

function actionLine(action: ModAction): string {
  const duration = action.durationMs === null ? "" : ` (${formatDuration(action.durationMs)})`;
  const by = action.moderatorId === null ? "" : ` by <@${action.moderatorId}>`;
  const when = time(action.createdAt, TimestampStyles.ShortDate);
  return `**${capitalize(action.action)}**${duration} · ${when}${by}\n> ${action.reason ?? NO_REASON}`;
}

/** One page of a member's moderation history, with account info and counts on every page. */
export function modlogEmbed(
  user: User,
  member: GuildMember | undefined,
  actions: readonly ModAction[],
  counts: ReadonlyMap<string, number>,
  page: number,
): { embed: EmbedBuilder; pageCount: number } {
  const current = paginate(actions, page, ACTIONS_PER_PAGE);
  const summary = [...counts].map(([action, count]) => `**${pluralLabel(action)}:** ${count}`);
  const joined = member?.joinedAt ? time(member.joinedAt, TimestampStyles.ShortDate) : "Not here";
  const built = embed(current.items.map(actionLine).join("\n\n") || "No actions recorded.")
    .setTitle(`Moderation log: ${member?.displayName ?? user.username}`)
    .setThumbnail(user.displayAvatarURL())
    .addFields(
      { name: "User ID", value: user.id, inline: true },
      {
        name: "Account created",
        value: time(user.createdAt, TimestampStyles.ShortDate),
        inline: true,
      },
      { name: "Joined server", value: joined, inline: true },
      { name: "Summary", value: summary.join("\n") || "No actions recorded", inline: false },
    );
  if (current.pageCount > 1) {
    built.setFooter({ text: `Page ${current.page} of ${current.pageCount}` });
  }
  return { embed: built, pageCount: current.pageCount };
}

export function describePunishment(term: BlockedTerm): string {
  const duration = term.durationMs === null ? "" : ` (${formatDuration(term.durationMs)})`;
  return `${capitalize(term.punishment)}${duration}`;
}

export function blockedTermsEmbed(
  terms: readonly BlockedTerm[],
  page: number,
): { embed: EmbedBuilder; pageCount: number } {
  const current = paginate(terms, page, TERMS_PER_PAGE);
  const built = embed(terms.length === 0 ? "No blocked terms in this server." : undefined)
    .setTitle("Blocked terms")
    .addFields(
      current.items.map((term) => ({
        name: term.term,
        value: `**Punishment:** ${describePunishment(term)}\n**Filtering:** ${term.advanced ? "Advanced" : "Basic"}`,
        inline: true,
      })),
    );
  if (current.pageCount > 1) {
    built.setFooter({ text: `Page ${current.page} of ${current.pageCount}` });
  }
  return { embed: built, pageCount: current.pageCount };
}
