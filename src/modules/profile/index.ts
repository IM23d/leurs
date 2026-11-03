import { defineModule } from "#core/module.ts";

import { avatarCommand } from "./commands/avatar.ts";
import { bannerCommand } from "./commands/banner.ts";

export const profileModule = defineModule({
  name: "profile",
  commands: [avatarCommand, bannerCommand],
});
