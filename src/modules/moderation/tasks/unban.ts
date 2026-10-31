import { z } from "zod";

import { defineTask } from "#core/tasks/define-task.ts";

import { postLog } from "../mod-log.ts";
import { logEntryEmbed } from "../moderation.views.ts";

const payload = z.object({ guildId: z.string(), userId: z.string() });

/** Lifts a timed ban from a blocked term. */
export const unbanTask = defineTask({
  kind: "moderation.unban",
  payload,
  run: async ({ guildId, userId }, client) => {
    const guild = client.guilds.cache.get(guildId);
    if (!guild) return;
    const user = await guild.bans.remove(userId, "Ban time is over").catch(() => null);
    if (!user) return;
    await postLog(
      guild,
      "blockedTermsLogChannelId",
      logEntryEmbed({ title: "Unban", target: user, moderator: null, reason: "Ban time is over" }),
    );
  },
});
