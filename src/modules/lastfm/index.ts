import { defineModule } from "#core/module.ts";

import { lastfmCommand } from "./commands/lastfm.ts";
import { npCommand } from "./commands/np.ts";

export const lastfmModule = defineModule({
  name: "lastfm",
  commands: [lastfmCommand, npCommand],
});
