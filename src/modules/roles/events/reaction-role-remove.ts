import { defineEvent } from "#core/events.ts";

import { reactionRoleFor } from "./reaction-member.ts";

export const reactionRoleRemoveEvent = defineEvent({
  name: "messageReactionRemove",
  run: async (reaction, user) => {
    const found = await reactionRoleFor(reaction, user);
    if (found?.member.roles.cache.has(found.role.id)) {
      await found.member.roles.remove(found.role, "Reaction role removed");
    }
  },
});
