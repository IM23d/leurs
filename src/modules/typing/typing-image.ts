import { createCanvas, type SKRSContext2D } from "@napi-rs/canvas";

import { fonts } from "#shared/ui/fonts.ts";

const FONT_FAMILY = fonts.regular;

const WIDTH = 1000;
const MIN_HEIGHT = 600;
const MARGIN = 50;
const FONT_SIZE = 24;
const LINE_HEIGHT = FONT_SIZE * 1.5;
const FONT = `${FONT_SIZE}px ${FONT_FAMILY}`;
const NOISE_LINES = 30;

function wrap(ctx: SKRSContext2D, words: readonly string[]): string[] {
  const maxWidth = WIDTH - 2 * MARGIN;
  const lines: string[][] = [[]];
  let lineWidth = 0;
  for (const word of words) {
    const width = ctx.measureText(`${word} `).width;
    if (lineWidth + width > maxWidth) {
      lines.push([]);
      lineWidth = 0;
    }
    lines.at(-1)?.push(word);
    lineWidth += width;
  }
  return lines.map((line) => line.join(" "));
}

/** Draws the words on white with random lines across them, so OCR can't just read the text. */
export async function renderWords(
  words: readonly string[],
  random: () => number = Math.random,
): Promise<Buffer> {
  const measure = createCanvas(WIDTH, 1).getContext("2d");
  measure.font = FONT;
  const lines = wrap(measure, words);
  // Long tests wrap to more lines than the default height holds, so the image grows to fit.
  const height = Math.max(MIN_HEIGHT, 2 * MARGIN + lines.length * LINE_HEIGHT);

  const canvas = createCanvas(WIDTH, height);
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#fff";
  ctx.fillRect(0, 0, WIDTH, height);

  ctx.font = FONT;
  ctx.textBaseline = "top";
  ctx.fillStyle = "#000";
  lines.forEach((line, index) => {
    ctx.fillText(line, MARGIN, MARGIN + index * LINE_HEIGHT);
  });

  const between = (min: number, max: number) => min + Math.floor(random() * (max - min + 1));
  ctx.lineWidth = 2;
  for (let index = 0; index < NOISE_LINES; index += 1) {
    ctx.strokeStyle = `rgb(${between(100, 200)}, ${between(100, 200)}, ${between(100, 200)})`;
    ctx.beginPath();
    ctx.moveTo(between(0, WIDTH), between(0, height));
    ctx.lineTo(between(0, WIDTH), between(0, height));
    ctx.stroke();
  }
  return canvas.encode("png");
}
