/** The old bot's default embed color, discord.py's light grey. */
export const DEFAULT_EMBED_COLOR = 0x97_9c_9f;

// The names the old bot accepted, with discord.py's values.
const NAMED_COLORS = new Map<string, number>([
  ["red", 0xe7_4c_3c],
  ["blue", 0x34_98_db],
  ["green", 0x2e_cc_71],
  ["yellow", 0xfe_e7_5c],
  ["orange", 0xe6_7e_22],
  ["purple", 0x9b_59_b6],
  ["gold", 0xf1_c4_0f],
  ["black", 0x00_00_00],
  ["white", 0xff_ff_ff],
  ["teal", 0x1a_bc_9c],
  ["magenta", 0xe9_1e_63],
  ["blurple", 0x58_65_f2],
  ["dark_blue", 0x20_66_94],
  ["dark_green", 0x1f_8b_4c],
  ["dark_red", 0x99_2d_22],
  ["dark_purple", 0x71_36_8a],
  ["dark_orange", 0xa8_43_00],
  ["dark_gold", 0xc2_7c_0e],
  ["dark_teal", 0x11_80_6a],
  ["dark_magenta", 0xad_14_57],
]);

/** Reads a hex code such as `#ff8800` or `ff8800`, or a color name such as `red`. */
export function parseColor(input: string): number | undefined {
  const text = input.trim().toLowerCase();
  const hex = /^#?([\da-f]{6})$/.exec(text)?.[1];
  return hex === undefined ? NAMED_COLORS.get(text) : Number.parseInt(hex, 16);
}
