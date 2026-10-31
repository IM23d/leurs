import { errorEmbed } from "#shared/ui/embeds.ts";
import { definePaginator, paginate } from "#shared/ui/paginator.ts";

import { findImages } from "../image-results.ts";
import { imageEmbed } from "../images.views.ts";

/** One image per page. The query lives in the button IDs. */
export const imagePages = definePaginator({
  id: "image-page",
  render: async ({ page, args }) => {
    // The custom ID splits on ":", so a query containing one arrives in parts.
    const query = args.join(":");
    const { items, page: current, pageCount } = paginate(await findImages(query), page, 1);
    const [image] = items;
    const shown = image
      ? imageEmbed(image, query, current, pageCount)
      : errorEmbed(`No images found for "${query}".`);
    return { embed: shown, pageCount };
  },
});
