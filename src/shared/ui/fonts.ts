import { fileURLToPath } from "node:url";

import { GlobalFonts } from "@napi-rs/canvas";

const fontPath = (file: string) =>
  fileURLToPath(new URL(`../../../assets/fonts/${file}`, import.meta.url));

/** Font families for images drawn with @napi-rs/canvas. Registered once on import. */
export const fonts = {
  regular: "Roboto",
  bold: "Roboto Bold",
} as const;

GlobalFonts.registerFromPath(fontPath("Roboto-Regular.ttf"), fonts.regular);
GlobalFonts.registerFromPath(fontPath("Roboto-Bold.ttf"), fonts.bold);
