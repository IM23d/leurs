import type { Module } from "#core/module.ts";
import { generalModule } from "#modules/general/index.ts";
import { settingsModule } from "#modules/settings/index.ts";

/** Every feature module the bot loads. Add a module here to enable it. */
export const modules: readonly Module[] = [generalModule, settingsModule];
