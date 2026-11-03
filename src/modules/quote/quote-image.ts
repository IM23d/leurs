import { createCanvas, loadImage, type SKRSContext2D } from "@napi-rs/canvas";

import { fonts } from "#shared/ui/fonts.ts";

const FONT = fonts.bold;

/** Layout size. The image is drawn at OUTPUT_SCALE times this for a sharp result. */
const SIZE = 1000;
const OUTPUT_SCALE = 2;
const WORDS_PER_LINE = 4;
const MAX_TEXT_WIDTH = SIZE * 0.8;
// Keeps long quotes clear of the name in the bottom right.
const MAX_TEXT_HEIGHT = SIZE * 0.6;
const LINE_HEIGHT = 1.2;

export interface QuoteInput {
  readonly avatar: Buffer;
  readonly text: string;
  readonly username: string;
}

/** Splits text into lines of a few words each, then wraps the whole quote in quotation marks. */
export function quoteLines(text: string): string[] {
  const words = text.split(/\s+/).filter((word) => word !== "");
  const lines = Array.from({ length: Math.ceil(words.length / WORDS_PER_LINE) }, (_, index) =>
    words.slice(index * WORDS_PER_LINE, (index + 1) * WORDS_PER_LINE).join(" "),
  );
  return lines.map(
    (line, index) => `${index === 0 ? '"' : ""}${line}${index === lines.length - 1 ? '"' : ""}`,
  );
}

const font = (size: number) => `bold ${size}px ${FONT}`;

function widest(ctx: SKRSContext2D, lines: readonly string[], size: number): number {
  ctx.font = font(size);
  return Math.max(...lines.map((line) => ctx.measureText(line).width));
}

/** The largest font size, in steps of 10, at which the quote still fits. */
function fitFontSize(ctx: SKRSContext2D, lines: readonly string[]): number {
  let size = 20;
  for (let next = 30; next < 500; next += 10) {
    const tooWide = widest(ctx, lines, next) > MAX_TEXT_WIDTH;
    const tooTall = lines.length * next * LINE_HEIGHT > MAX_TEXT_HEIGHT;
    if (tooWide || tooTall) break;
    size = next;
  }
  return size;
}

function drawWithShadow(ctx: SKRSContext2D, text: string, x: number, y: number, offset: number) {
  ctx.fillStyle = "#000";
  for (const [dx, dy] of [
    [offset, offset],
    [-offset, offset],
    [offset, -offset],
    [-offset, -offset],
  ] as const) {
    ctx.fillText(text, x + dx, y + dy);
  }
  ctx.fillStyle = "#fff";
  ctx.fillText(text, x, y);
}

function drawAvatar(ctx: SKRSContext2D, avatar: Awaited<ReturnType<typeof loadImage>>) {
  const side = Math.min(avatar.width, avatar.height);
  const sx = (avatar.width - side) / 2;
  const sy = (avatar.height - side) / 2;
  ctx.drawImage(avatar, sx, sy, side, side, 0, 0, SIZE, SIZE);
  ctx.fillStyle = "rgba(0, 0, 0, 0.9)";
  ctx.fillRect(0, 0, SIZE, SIZE);
}

/** Draws the quote over a darkened, square crop of the avatar, with the name in the corner. */
export async function renderQuote({ avatar, text, username }: QuoteInput): Promise<Buffer> {
  const canvas = createCanvas(SIZE * OUTPUT_SCALE, SIZE * OUTPUT_SCALE);
  const ctx = canvas.getContext("2d");
  ctx.scale(OUTPUT_SCALE, OUTPUT_SCALE);
  drawAvatar(ctx, await loadImage(avatar));

  ctx.textBaseline = "top";
  const lines = quoteLines(text);
  const fontSize = fitFontSize(ctx, lines);
  const shadow = Math.max(3, Math.floor(fontSize / 20));
  const lineHeight = fontSize * LINE_HEIGHT;
  const blockWidth = widest(ctx, lines, fontSize);
  const x = (SIZE - blockWidth) / 2;
  const top = (SIZE - lines.length * lineHeight) / 2 - SIZE / 8;
  lines.forEach((line, index) => {
    drawWithShadow(ctx, line, x, top + index * lineHeight, shadow);
  });

  const name = `- ${username}`;
  ctx.font = font(Math.floor(fontSize / 2));
  const nameX = SIZE - ctx.measureText(name).width - SIZE / 20;
  drawWithShadow(ctx, name, nameX, SIZE - SIZE / 5, Math.floor(shadow / 2));

  return canvas.encode("png");
}
