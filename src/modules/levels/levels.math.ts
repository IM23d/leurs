export const XP_PER_LEVEL = 3500;
export const BASE_MESSAGE_XP = 15;
const MESSAGE_XP_SPREAD = 5;

export const levelForXp = (xp: number): number => Math.floor(xp / XP_PER_LEVEL);

/** XP for one message: 10 to 20, evenly spread. `random` returns a number in [0, 1). */
export const rollMessageXp = (random: () => number = Math.random): number =>
  BASE_MESSAGE_XP - MESSAGE_XP_SPREAD + Math.floor(random() * (2 * MESSAGE_XP_SPREAD + 1));

export interface LevelProgress {
  level: number;
  /** XP earned since the current level started. */
  current: number;
  /** XP the next level takes in total. */
  needed: number;
  /** Whole percent, 0 to 100. */
  percent: number;
}

export function levelProgress(xp: number): LevelProgress {
  const level = levelForXp(xp);
  const current = xp - level * XP_PER_LEVEL;
  return {
    level,
    current,
    needed: XP_PER_LEVEL,
    percent: Math.floor((current / XP_PER_LEVEL) * 100),
  };
}
