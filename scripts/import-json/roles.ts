import { z } from "zod";

import { addReactionRole } from "#modules/roles/reaction-roles.service.ts";
import { saveBackup } from "#modules/roles/role-backups.service.ts";
import { parseEmoji } from "#shared/lib/emoji.ts";

import type { Importer, LegacySource } from "./source.ts";

const SNOWFLAKE = /^\d{17,20}$/;

// The old bot wrote role IDs as JSON numbers. Large ones arrive as strings (see source.ts).
const snowflake = z.union([
  z.string().regex(SNOWFLAKE),
  z.number().refine(Number.isSafeInteger).transform(String).pipe(z.string().regex(SNOWFLAKE)),
]);

const nested = <T extends z.ZodType>(inner: T) =>
  z.record(z.string(), z.record(z.string(), inner).catch({}));

// saved_roles.json: { "<guildId>": { "<userId>": [<roleId>, ...] } }
const backup = z.object({
  guildId: z.string().regex(SNOWFLAKE),
  userId: z.string().regex(SNOWFLAKE),
  roleIds: z.array(snowflake),
});

// reaction_roles.json: { "<guildId>": { "<messageId>": { "<emoji>": <roleId> } } }
const reactionRole = z.object({
  guildId: z.string().regex(SNOWFLAKE),
  messageId: z.string().regex(SNOWFLAKE),
  emoji: z
    .string()
    .transform((text, ctx) => parseEmoji(text) ?? (ctx.addIssue("not an emoji"), z.NEVER)),
  roleId: snowflake,
});

// roles_info.json: { "last_save": "<naive UTC ISO time>", "next_save": ... }
const info = z.object({ last_save: z.string().nullish() }).catch({});

function lastSave(source: LegacySource): Date {
  const text = info.parse(source.read("roles_info.json") ?? {}).last_save;
  const date = text ? new Date(/[Z+]/.test(text) ? text : `${text}Z`) : new Date(Number.NaN);
  return Number.isNaN(date.getTime()) ? new Date() : date;
}

function valid<T>(results: readonly z.ZodSafeParseResult<T>[], what: string): T[] {
  const data = results.flatMap((result) => (result.success ? [result.data] : []));
  const skipped = results.length - data.length;
  if (skipped > 0) console.warn(`roles: skipped ${skipped} malformed ${what}`);
  return data;
}

function importBackups(source: LegacySource): number {
  const data = nested(z.unknown()).optional().parse(source.read("saved_roles.json")) ?? {};
  const results = Object.entries(data).flatMap(([guildId, members]) =>
    Object.entries(members).map(([userId, roleIds]) =>
      backup.safeParse({ guildId, userId, roleIds }),
    ),
  );
  const savedAt = lastSave(source);
  const backups = valid(results, "role backups").filter(({ roleIds }) => roleIds.length > 0);
  backups.forEach(({ guildId, ...member }) => {
    saveBackup(guildId, member, savedAt);
  });
  return backups.length;
}

function importReactionRoles(source: LegacySource): number {
  const data =
    nested(z.record(z.string(), z.unknown()).catch({}))
      .optional()
      .parse(source.read("reaction_roles.json")) ?? {};
  const results = Object.entries(data).flatMap(([guildId, messages]) =>
    Object.entries(messages).flatMap(([messageId, emojis]) =>
      Object.entries(emojis).map(([emoji, roleId]) =>
        reactionRole.safeParse({ guildId, messageId, emoji, roleId }),
      ),
    ),
  );
  const links = valid(results, "reaction roles");
  links.forEach(({ emoji, ...link }) => {
    addReactionRole({ ...link, channelId: null, emojiKey: emoji.key, emoji: emoji.text });
  });
  return links.length;
}

export const rolesImporter: Importer = {
  name: "roles",
  run: (source) => importBackups(source) + importReactionRoles(source),
};
