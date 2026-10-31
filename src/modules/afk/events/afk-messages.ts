import { defineEvent } from "#core/events.ts";
import { embed } from "#shared/ui/embeds.ts";

import { afkStore, formatAway } from "../afk.service.ts";

/** Clears the AFK status of people who talk, and tells people when they mention someone AFK. */
export const afkMessages = defineEvent({
  name: "messageCreate",
  run: async (message) => {
    if (message.author.bot || !message.inGuild()) return;
    const now = Date.now();
    const back = afkStore.returnFrom(message.author.id, message.createdTimestamp);
    if (back) {
      await message.channel.send({
        embeds: [
          embed(
            `Welcome back ${message.author.toString()}. You were AFK for ${formatAway(now - back.since)}.`,
          ),
        ],
      });
    }
    const notices = message.mentions.users
      .filter((user) => user.id !== message.author.id)
      .map((user) => ({ user, status: afkStore.get(user.id) }))
      .flatMap(({ user, status }) =>
        status
          ? [
              `${user.toString()} is AFK: ${status.reason}. Away for ${formatAway(now - status.since)}.`,
            ]
          : [],
      );
    if (notices.length > 0) {
      await message.reply({
        embeds: [embed(notices.join("\n"))],
        allowedMentions: { repliedUser: false },
      });
    }
  },
});
