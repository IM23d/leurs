import { defineCommand } from "#core/commands/define.ts";
import { opt } from "#core/commands/options.ts";
import { embed } from "#shared/ui/embeds.ts";

import { afkStore } from "../afk.service.ts";

const MAX_REASON_LENGTH = 200;

export const afkCommand = defineCommand({
  name: "afk",
  description: "Tell people who mention you that you're away",
  options: { reason: opt.string("Why you're away").max(MAX_REASON_LENGTH).rest().optional() },
  run: async (ctx, { reason = "AFK" }) => {
    afkStore.set(ctx.user.id, reason);
    await ctx.reply(embed(`${ctx.user.toString()} is now AFK: ${reason}`));
  },
});
