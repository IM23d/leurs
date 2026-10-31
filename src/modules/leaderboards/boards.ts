import { balanceRanking } from "#modules/economy/api.ts";
import { levelRanking, voiceRanking } from "#modules/levels/api.ts";
import { formatDuration } from "#shared/lib/duration.ts";

export interface Board {
  readonly title: string;
  readonly empty: string;
  /** One line per user, best first, as [userId, value text]. */
  readonly rank: (userIds: readonly string[]) => (readonly [string, string])[];
}

const number = (value: number) => value.toLocaleString("en-US");

export const boards = {
  levels: {
    title: "Level leaderboard",
    empty: "Nobody here has any XP yet.",
    rank: (userIds) =>
      levelRanking(userIds).map(
        (row) => [row.userId, `Level ${row.level} · ${number(row.xp)} XP`] as const,
      ),
  },
  voice: {
    title: "Voice leaderboard",
    empty: "Nobody here has spent time in voice yet.",
    rank: (userIds) =>
      voiceRanking(userIds).map((row) => [row.userId, formatDuration(row.seconds * 1000)] as const),
  },
  money: {
    title: "Balance leaderboard",
    empty: "Nobody here has any coins yet.",
    rank: (userIds) =>
      balanceRanking(userIds).map((row) => [row.userId, `${number(row.balance)} coins`] as const),
  },
} as const satisfies Record<string, Board>;

export type BoardName = keyof typeof boards;

export const isBoardName = (name: string): name is BoardName => name in boards;
