import type { Module } from "#core/module.ts";
import { afkModule } from "#modules/afk/index.ts";
import { aiModule } from "#modules/ai/index.ts";
import { birthdaysModule } from "#modules/birthdays/index.ts";
import { clownboardModule } from "#modules/clownboard/index.ts";
import { economyModule } from "#modules/economy/index.ts";
import { funModule } from "#modules/fun/index.ts";
import { generalModule } from "#modules/general/index.ts";
import { imagesModule } from "#modules/images/index.ts";
import { lastfmModule } from "#modules/lastfm/index.ts";
import { leaderboardsModule } from "#modules/leaderboards/index.ts";
import { levelsModule } from "#modules/levels/index.ts";
import { moderationModule } from "#modules/moderation/index.ts";
import { profileModule } from "#modules/profile/index.ts";
import { quoteModule } from "#modules/quote/index.ts";
import { reactionLogModule } from "#modules/reaction-log/index.ts";
import { remindersModule } from "#modules/reminders/index.ts";
import { rolesModule } from "#modules/roles/index.ts";
import { settingsModule } from "#modules/settings/index.ts";
import { snipeModule } from "#modules/snipe/index.ts";
import { timezonesModule } from "#modules/timezones/index.ts";
import { toolsModule } from "#modules/tools/index.ts";
import { typingModule } from "#modules/typing/index.ts";
import { voiceLogModule } from "#modules/voice-log/index.ts";
import { weatherModule } from "#modules/weather/index.ts";
import { wordleModule } from "#modules/wordle/index.ts";

/** Every feature module the bot loads, in the order /help lists them. Add a module here to enable it. */
export const modules: readonly Module[] = [
  generalModule,
  settingsModule,
  levelsModule,
  voiceLogModule,
  leaderboardsModule,
  economyModule,
  moderationModule,
  rolesModule,
  toolsModule,
  remindersModule,
  afkModule,
  snipeModule,
  reactionLogModule,
  clownboardModule,
  birthdaysModule,
  timezonesModule,
  profileModule,
  quoteModule,
  weatherModule,
  typingModule,
  wordleModule,
  funModule,
  lastfmModule,
  aiModule,
  imagesModule,
];
