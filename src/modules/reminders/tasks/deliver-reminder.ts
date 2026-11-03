import { z } from "zod";

import { defineTask } from "#core/tasks/define-task.ts";
import { logger } from "#shared/lib/logger.ts";
import { embed } from "#shared/ui/embeds.ts";

const reminderPayload = z.object({
  userId: z.string(),
  channelId: z.string(),
  reason: z.string(),
});

/** Pings the user in the channel where they set the reminder, or DMs them if that fails. */
export const reminderTask = defineTask({
  kind: "reminder",
  payload: reminderPayload,
  run: async ({ userId, channelId, reason }, client) => {
    const reminder = embed(reason).setTitle("Reminder");
    const channel = await client.channels.fetch(channelId).catch(() => null);
    if (channel?.isSendable()) {
      try {
        await channel.send({
          content: `<@${userId}>`,
          embeds: [reminder],
          allowedMentions: { users: [userId] },
        });
        return;
      } catch (error) {
        logger.warn({ err: error, channelId }, "Could not post a reminder, sending it as a DM");
      }
    }
    const user = await client.users.fetch(userId);
    await user.send({ embeds: [reminder] });
  },
});
