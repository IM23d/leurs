import { defineModule } from "#core/module.ts";

import { imageCommand } from "./commands/image.ts";
import { imagePages } from "./components/image-pages.ts";

export const imagesModule = defineModule({
  name: "images",
  commands: [imageCommand],
  components: [imagePages.component],
});
