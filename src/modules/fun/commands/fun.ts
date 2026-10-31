import { defineCommand, subcommand } from "#core/commands/define.ts";

import { randomLyric } from "../lyrics.service.ts";

const say = (description: string, text: string, alias: string) =>
  subcommand({
    description,
    aliases: [alias],
    run: async (ctx) => {
      await ctx.reply(text);
    },
  });

export const funCommand = defineCommand({
  name: "fun",
  description: "In-jokes from the old bot",
  subcommands: {
    code: say(
      "Post the code",
      "zgte5dr6ftgzhujikokztrdeswa536edfr65fm ,WU83 34 FTZFTBFTBF7677U6",
      "code",
    ),
    geschichte: say(
      "Tell the story",
      "ich habe mal david in migros getroffen und ein foto mit david gemacht. das hat mich glücklich gemacht. dann hatten wir französisch...",
      "geschichte",
    ),
    hi: say("Say hi", "Hi I'm coffee!", "hi"),
    lyric: subcommand({
      description: "Post a random lyric",
      aliases: ["lyric"],
      run: async (ctx) => {
        await ctx.reply(await randomLyric());
      },
    }),
  },
});
