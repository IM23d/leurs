import { defineEvent } from "#core/events.ts";

import { reactionRoleFor } from "./reaction-member.ts";

export const reactionRoleAddEvent = defineEvent({
  name: "messageReactionAdd",
  run: async (reaction, user) => {
    const found = await reactionRoleFor(reaction, user);
    if (found && !found.member.roles.cache.has(found.role.id)) {
      await found.member.roles.add(found.role, "Reaction role");
    }
  },
});
