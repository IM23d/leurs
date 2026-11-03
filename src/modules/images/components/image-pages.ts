import { errorEmbed } from "#shared/ui/embeds.ts";
import { definePaginator, paginate } from "#shared/ui/paginator.ts";

import { findImages } from "../image-results.ts";
import { imageEmbed } from "../images.views.ts";

// One letter each, because the custom ID has little room left after a 60-character query.
const SAFE = "s";
const UNFILTERED = "u";

/** Button arguments: the SafeSearch mode, then the query. */
export const imagePageArgs = (query: string, safe: boolean): string[] => [
  safe ? SAFE : UNFILTERED,
  query,
];

/** One image per page. The SafeSearch mode and the query live in the button IDs. */
export const imagePages = definePaginator({
  id: "image-page",
  render: async ({ page, args: [mode, ...parts] }) => {
    // The custom ID splits on ":", so a query containing one arrives in parts.
    const query = parts.join(":");
    // Anything but the explicit unfiltered mode searches safely.
    const results = await findImages(query, mode !== UNFILTERED);
    const { items, page: current, pageCount } = paginate(results, page, 1);
    const [image] = items;
    const shown = image
      ? imageEmbed(image, query, current, pageCount)
      : errorEmbed(`No images found for "${query}".`);
    return { embed: shown, pageCount };
  },
});
