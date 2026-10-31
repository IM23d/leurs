import { defineCommand } from "#core/commands/define.ts";
import { embed } from "#shared/ui/embeds.ts";

export const aboutCommand = defineCommand({
  name: "about",
  description: "About leurs",
  aliases: ["info"],
  run: async (ctx) => {
    await ctx.reply(
      embed("A Discord bot with levels, economy, moderation and utility commands.")
        .setTitle("leurs")
        .addFields(
          { name: "Source", value: "https://github.com/IM23d/leurs", inline: false },
          { name: "Docs", value: "https://docs.leurs.ch", inline: false },
          { name: "Developers", value: "@bettercallmilan, @reazndev", inline: true },
          { name: "Contributors", value: "@lhilfiker, @PianoNic", inline: true },
          { name: "Was also there", value: "@seakyy", inline: true },
        ),
    );
  },
});
