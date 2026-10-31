import { UserError } from "#core/errors.ts";

import { getUsername } from "./lastfm.service.ts";

/** The Last.fm name linked to a user, or a UserError telling them how to link one. */
export function linkedUsername(userId: string, askedBy: string, prefix: string): string {
  const username = getUsername(userId);
  if (username !== undefined) return username;
  throw new UserError(
    userId === askedBy
      ? `You haven't linked Last.fm yet. Use \`${prefix}lastfm link <username>\`.`
      : `<@${userId}> hasn't linked Last.fm yet.`,
  );
}
